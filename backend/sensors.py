"""
스마트 온실 시스템의 센서 데이터 관리 모듈
실제 아두이노 센서 연동 및 시뮬레이션 지원
"""
import random
import time
import threading
import re
from datetime import datetime, timedelta
import numpy as np

# 아두이노 연결을 위한 추가 임포트
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    print("pyserial이 설치되지 않았습니다. 시뮬레이션 모드로만 동작합니다.")
    SERIAL_AVAILABLE = False

class SensorDataManager:
    """센서 데이터를 관리하는 클래스 (실제 하드웨어 + 시뮬레이션 지원)"""
    
    def __init__(self, use_arduino=True, init_values=None):
        """
        센서 데이터 매니저를 초기화합니다.
        
        Args:
            use_arduino (bool): 아두이노 연결 시도 여부. 기본값은 True.
            init_values (dict, optional): 센서 초기값. 기본값은 None.
        """
        # 기본 초기값 설정
        self.current_values = {
            "temperature": 23.5,  # 섭씨
            "humidity": 58.0,     # 퍼센트 (아두이노에서 지원하지 않으면 계산값 사용)
            "power": 135.0,       # 와트 (장치 상태로부터 계산)
            "soil": 42.0,         # 퍼센트
        }
        
        # 제공된 초기값이 있으면 업데이트
        if init_values:
            for key, value in init_values.items():
                if key in self.current_values:
                    self.current_values[key] = value
        
        # 장치 상태 초기화 (MyApp 기준)
        self.device_status = {
            "fan": False,     # 팬
            "water": False,   # 급수펌프
            "light": False,   # LED조명
            "window": False   # 창문
        }
        
        # 아두이노 관련 변수
        self.arduino = None
        self.arduino_connected = False
        self.use_arduino = use_arduino and SERIAL_AVAILABLE
        self.data_lock = threading.Lock()
        self.arduino_sensor_data = {}
        
        # 히스토리 데이터 초기화
        self.history = {
            "temperature": [],
            "humidity": [],
            "power": [],
            "soil": []
        }
        
        # 아두이노 연결 시도
        if self.use_arduino:
            self._connect_arduino()
            if self.arduino_connected:
                self._start_arduino_reader()
        
        # 24시간 더미 히스토리 데이터 생성
        self._generate_initial_history()
        
        print(f"센서 매니저 초기화 완료 - 아두이노 연결: {'성공' if self.arduino_connected else '실패 (시뮬레이션 모드)'}")
    
    def _connect_arduino(self):
        """아두이노 연결을 시도합니다."""
        if not SERIAL_AVAILABLE:
            return False
            
        try:
            # 사용 가능한 포트 목록 가져오기
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            print(f"사용 가능한 포트들: {available_ports}")
            
            # 아두이노 관련 포트들을 우선적으로 필터링
            arduino_ports = []
            for port in available_ports:
                if any(keyword in port.lower() for keyword in ['usbmodem', 'usbserial', 'ttyusb', 'ttyacm', 'com']):
                    arduino_ports.append(port)
            
            print(f"아두이노 관련 포트들: {arduino_ports}")
            
            # 아두이노 포트들 시도
            for port in arduino_ports:
                try:
                    print(f"아두이노 포트 {port} 연결 시도 중...")
                    self.arduino = serial.Serial(port, 9600, timeout=1)
                    time.sleep(3)  # 아두이노 초기화 대기
                    
                    # 통신 테스트
                    if self._test_arduino_communication():
                        self.arduino_connected = True
                        print(f"아두이노가 {port}에 성공적으로 연결되었습니다.")
                        return True
                    else:
                        print(f"포트 {port}에서 통신 테스트 실패")
                        self.arduino.close()
                        self.arduino = None
                        
                except Exception as e:
                    print(f"포트 {port} 연결 실패: {e}")
                    if self.arduino:
                        try:
                            self.arduino.close()
                        except:
                            pass
                        self.arduino = None
            
            print("아두이노 연결 실패 - 시뮬레이션 모드로 전환")
            return False
        except Exception as e:
            print(f"아두이노 연결 오류: {e}")
            return False
    
    def _test_arduino_communication(self):
        """아두이노 통신을 테스트합니다."""
        if not self.arduino:
            return False
        
        try:
            # 버퍼 비우기
            self.arduino.flushInput()
            self.arduino.flushOutput()
            
            # STATUS 명령 전송
            self.arduino.write(b"STATUS\n")
            self.arduino.flush()
            
            # 응답 대기
            received_data = []
            for i in range(50):  # 5초 동안 0.1초씩 체크
                if self.arduino.in_waiting > 0:
                    try:
                        line = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            received_data.append(line)
                            if "시스템 상태" in line or "온도:" in line:
                                return True
                    except Exception as e:
                        print(f"통신 테스트 읽기 오류: {e}")
                time.sleep(0.1)
            
            return len(received_data) > 0
        except Exception as e:
            print(f"통신 테스트 오류: {e}")
            return False
    
    def _start_arduino_reader(self):
        """아두이노 데이터 읽기 스레드를 시작합니다."""
        if not self.arduino_connected:
            return
        
        def read_arduino_data():
            while self.arduino_connected and self.arduino:
                try:
                    if self.arduino.in_waiting > 0:
                        line = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            self._parse_arduino_data(line)
                except Exception as e:
                    print(f"아두이노 데이터 읽기 오류: {e}")
                    # 연결 문제 시 재연결 시도
                    if "device reports readiness to read but returned no data" in str(e).lower():
                        print("아두이노 연결 끊김 감지 - 시뮬레이션 모드로 전환")
                        self.arduino_connected = False
                        break
                time.sleep(0.1)
        
        # 데이터 읽기 스레드 시작
        reader_thread = threading.Thread(target=read_arduino_data, daemon=True)
        reader_thread.start()
    
    def _parse_arduino_data(self, data_line):
        """아두이노에서 받은 데이터를 파싱합니다."""
        try:
            # "온도: 25.0 °C, CO2: 350, 조도: 15, 토양 수분: 650" 형태의 데이터 파싱
            with self.data_lock:
                temp_match = re.search(r'온도:\s*([\d.]+)', data_line)
                co2_match = re.search(r'CO2:\s*(\d+)', data_line)
                light_match = re.search(r'조도:\s*(\d+)', data_line)
                soil_match = re.search(r'토양\s*수분:\s*(\d+)', data_line)
                
                if temp_match:
                    self.arduino_sensor_data['temperature'] = float(temp_match.group(1))
                if co2_match:
                    self.arduino_sensor_data['co2'] = int(co2_match.group(1))
                if light_match:
                    self.arduino_sensor_data['light'] = int(light_match.group(1))
                if soil_match:
                    # 아두이노의 토양수분 값을 퍼센트로 변환 (0-1023 → 0-100)
                    soil_raw = int(soil_match.group(1))
                    self.arduino_sensor_data['soil'] = round(max(0, 100 - (soil_raw / 1023 * 100)), 1)
                
        except Exception as e:
            print(f"아두이노 데이터 파싱 오류: {e}")
    
    def _send_arduino_command(self, command):
        """아두이노에 명령을 전송합니다."""
        if not self.arduino_connected or not self.arduino:
            return False
        
        try:
            self.arduino.write(f"{command}\n".encode())
            self.arduino.flush()
            print(f"아두이노 명령 전송: {command}")
            return True
        except Exception as e:
            print(f"아두이노 명령 전송 오류: {e}")
            return False
    
    def _generate_initial_history(self):
        """24시간의 초기 히스토리 데이터를 생성합니다."""
        now = datetime.now()
        for i in range(24):
            time_point = now - timedelta(hours=24-i)
            timestamp = time_point.strftime("%Y-%m-%d %H:00:00")
            
            # 각 센서마다 약간의 변동을 주어 데이터 생성
            self.history["temperature"].append({
                "timestamp": timestamp, 
                "value": round(self.current_values["temperature"] + np.random.uniform(-2, 2), 1)
            })
            self.history["humidity"].append({
                "timestamp": timestamp, 
                "value": round(self.current_values["humidity"] + np.random.uniform(-5, 5), 1)
            })
            self.history["power"].append({
                "timestamp": timestamp, 
                "value": round(self.current_values["power"] + np.random.uniform(-10, 10), 1)
            })
            self.history["soil"].append({
                "timestamp": timestamp, 
                "value": round(self.current_values["soil"] + np.random.uniform(-3, 3), 1)
            })
    
    def _calculate_power_consumption(self):
        """장치 상태를 기반으로 전력 소모량을 계산합니다."""
        base_power = 50.0  # 기본 전력 (W)
        device_power = {
            "fan": 25.0,      # 팬 전력
            "water": 15.0,    # 펌프 전력  
            "light": 40.0,    # LED 전력
            "window": 5.0     # 서보모터 전력
        }
        
        total_power = base_power
        for device, status in self.device_status.items():
            if status and device in device_power:
                total_power += device_power[device]
        
        return round(total_power + np.random.uniform(-5, 5), 1)
    
    def _calculate_humidity(self):
        """온도와 장치 상태를 기반으로 습도를 추정합니다."""
        # 기본 습도 계산 (실제 DHT11 센서로 교체 가능)
        base_humidity = 58.0
        
        # 창문 열림 시 외부 습도와 균형
        if self.device_status["window"]:
            external_humidity = 50 + np.random.uniform(-10, 10)
            base_humidity = 0.9 * base_humidity + 0.1 * external_humidity
        
        # 온도에 따른 상대습도 변화
        if 'temperature' in self.arduino_sensor_data:
            temp = self.arduino_sensor_data['temperature']
            if temp > 25:
                base_humidity -= (temp - 25) * 2
            elif temp < 20:
                base_humidity += (20 - temp) * 1.5
        
        return round(max(20, min(100, base_humidity)), 1)
    
    def update_sensor_values(self):
        """센서 값을 업데이트하고 현재 값을 반환합니다."""
        if self.arduino_connected:
            # 아두이노 연결 시 실제 센서 데이터 사용
            with self.data_lock:
                if 'temperature' in self.arduino_sensor_data:
                    self.current_values["temperature"] = self.arduino_sensor_data['temperature']
                
                if 'soil' in self.arduino_sensor_data:
                    self.current_values["soil"] = self.arduino_sensor_data['soil']
                
                # 습도는 계산값 사용 (또는 아두이노 DHT11에서 습도도 읽도록 수정 가능)
                self.current_values["humidity"] = self._calculate_humidity()
                
                # 전력은 장치 상태로부터 계산
                self.current_values["power"] = self._calculate_power_consumption()
        else:
            # 시뮬레이션 모드
            self.current_values["temperature"] = round(self.current_values["temperature"] + np.random.uniform(-0.5, 0.5), 1)
            self.current_values["humidity"] = round(self.current_values["humidity"] + np.random.uniform(-1, 1), 1)
            self.current_values["power"] = round(self.current_values["power"] + np.random.uniform(-2, 2), 1)
            self.current_values["soil"] = round(self.current_values["soil"] + np.random.uniform(-0.5, 0.5), 1)
            
            # 장치 상태에 따른 값 변화 시뮬레이션
            if self.device_status["fan"]:
                self.current_values["temperature"] -= 0.2
                self.current_values["power"] += 5.0
            
            if self.device_status["water"]:
                self.current_values["soil"] += 0.5
                self.current_values["power"] += 3.0
            
            if self.device_status["light"]:
                self.current_values["temperature"] += 0.1
                self.current_values["power"] += 10.0
            
            if self.device_status["window"]:
                external_humidity = 50 + np.random.uniform(-10, 10)
                self.current_values["humidity"] = round(
                    0.9 * self.current_values["humidity"] + 0.1 * external_humidity, 1
                )
        
        # 값 범위 제한
        self.current_values["temperature"] = max(min(self.current_values["temperature"], 40), 10)
        self.current_values["humidity"] = max(min(self.current_values["humidity"], 100), 20)
        self.current_values["power"] = max(min(self.current_values["power"], 300), 50)
        self.current_values["soil"] = max(min(self.current_values["soil"], 100), 0)
        
        return self.current_values
    
    def update_device(self, device, status):
        """장치 상태를 업데이트합니다."""
        if device not in self.device_status:
            return False
        
        old_status = self.device_status[device]
        self.device_status[device] = status
        
        # 아두이노 연결 시 실제 제어 명령 전송
        if self.arduino_connected and old_status != status:
            # MyApp 장치명을 아두이노 명령으로 매핑
            device_mapping = {
                "fan": "FAN",
                "water": "PUMP",  # 급수 → 펌프
                "light": "LED",   # 조명 → LED
                "window": "WINDOW"
            }
            
            if device in device_mapping:
                arduino_device = device_mapping[device]
                command = f"MANUAL_{arduino_device}_{'ON' if status else 'OFF'}"
                self._send_arduino_command(command)
        
        return True
    
    def get_history(self, metric):
        """특정 항목의 기록 데이터를 반환합니다."""
        if metric in self.history:
            return self.history[metric]
        return []
    
    def add_history_data_point(self):
        """현재 센서 값을 기록 데이터에 추가합니다. 매 시간마다 호출합니다."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:00:00")
        
        for metric in self.current_values:
            self.history[metric].append({
                "timestamp": timestamp,
                "value": self.current_values[metric]
            })
            
            # 기록을 24시간으로 제한
            if len(self.history[metric]) > 24:
                self.history[metric].pop(0)
    
    def get_arduino_status(self):
        """아두이노 연결 상태를 반환합니다."""
        return {
            "connected": self.arduino_connected,
            "port": self.arduino.port if self.arduino else None,
            "mode": "하드웨어" if self.arduino_connected else "시뮬레이션"
        }
    
    def reconnect_arduino(self):
        """아두이노 재연결을 시도합니다."""
        if self.arduino:
            try:
                self.arduino.close()
            except:
                pass
            self.arduino = None
        
        self.arduino_connected = False
        
        if self.use_arduino:
            self._connect_arduino()
            if self.arduino_connected:
                self._start_arduino_reader()
        
        return self.arduino_connected

# 하위 호환성을 위한 별칭 (기존 코드가 동작하도록)
SensorDataSimulator = SensorDataManager

# 싱글톤 인스턴스 (아두이노 연결 시도)
simulator = SensorDataManager(use_arduino=True) 