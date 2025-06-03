#!/usr/bin/env python3
"""
아두이노 연결 테스트 스크립트
"""
import time
from sensors import SensorDataManager

def test_arduino_connection():
    """아두이노 연결을 테스트합니다."""
    print("🔌 아두이노 연결 테스트 시작...")
    print("=" * 50)
    
    # 센서 매니저 초기화 (아두이노 연결 시도)
    sensor_manager = SensorDataManager(use_arduino=True)
    
    # 연결 상태 확인
    status = sensor_manager.get_arduino_status()
    print(f"📊 연결 상태: {status}")
    
    if status['connected']:
        print("✅ 아두이노 연결 성공!")
        print(f"📱 포트: {status['port']}")
        print(f"🔧 모드: {status['mode']}")
        
        # 센서 데이터 테스트
        print("\n📡 센서 데이터 읽기 테스트...")
        for i in range(10):
            values = sensor_manager.update_sensor_values()
            print(f"[{i+1:2d}] 온도: {values['temperature']:5.1f}°C | "
                  f"습도: {values['humidity']:5.1f}% | "
                  f"토양: {values['soil']:5.1f}% | "
                  f"전력: {values['power']:6.1f}W")
            time.sleep(2)
        
        # 장치 제어 테스트
        print("\n🎛️  장치 제어 테스트...")
        test_devices = ['fan', 'light', 'water', 'window']
        
        for device in test_devices:
            print(f"\n{device.upper()} 제어 테스트:")
            
            # 켜기
            print(f"  └ {device} 켜기...")
            sensor_manager.update_device(device, True)
            time.sleep(2)
            
            # 끄기
            print(f"  └ {device} 끄기...")
            sensor_manager.update_device(device, False)
            time.sleep(2)
        
        print("\n✅ 모든 테스트 완료!")
        
    else:
        print("❌ 아두이노 연결 실패!")
        print("💡 아두이노가 연결되어 있는지 확인하세요.")
        print("💡 포트 권한을 확인하세요.")
        print("💡 아두이노에 올바른 펌웨어가 업로드되어 있는지 확인하세요.")
        
        # 시뮬레이션 모드 테스트
        print("\n🎭 시뮬레이션 모드로 테스트...")
        for i in range(5):
            values = sensor_manager.update_sensor_values()
            print(f"[{i+1}] 온도: {values['temperature']:5.1f}°C | "
                  f"습도: {values['humidity']:5.1f}% | "
                  f"토양: {values['soil']:5.1f}% | "
                  f"전력: {values['power']:6.1f}W")
            time.sleep(1)

def manual_arduino_test():
    """수동 아두이노 테스트 (명령 입력)"""
    print("🎮 수동 아두이노 테스트 모드")
    print("명령어 예시:")
    print("  - fan on/off : 팬 제어")
    print("  - light on/off : LED 제어") 
    print("  - water on/off : 펌프 제어")
    print("  - window on/off : 창문 제어")
    print("  - status : 센서 상태 확인")
    print("  - quit : 종료")
    print("=" * 50)
    
    sensor_manager = SensorDataManager(use_arduino=True)
    
    if not sensor_manager.get_arduino_status()['connected']:
        print("❌ 아두이노가 연결되지 않았습니다!")
        return
    
    while True:
        try:
            command = input("\n명령어 입력: ").strip().lower()
            
            if command == 'quit':
                break
            elif command == 'status':
                values = sensor_manager.update_sensor_values()
                print(f"📊 센서 상태:")
                print(f"  온도: {values['temperature']}°C")
                print(f"  습도: {values['humidity']}%")
                print(f"  토양: {values['soil']}%")
                print(f"  전력: {values['power']}W")
                print(f"🎛️  장치 상태: {sensor_manager.device_status}")
            elif command.startswith(('fan', 'light', 'water', 'window')):
                parts = command.split()
                if len(parts) == 2:
                    device, action = parts
                    if action in ['on', 'off']:
                        status = action == 'on'
                        sensor_manager.update_device(device, status)
                        print(f"✅ {device.upper()} {'켜짐' if status else '꺼짐'}")
                    else:
                        print("❌ on 또는 off만 입력 가능합니다.")
                else:
                    print("❌ 잘못된 명령어 형식입니다.")
            else:
                print("❌ 알 수 없는 명령어입니다.")
                
        except KeyboardInterrupt:
            print("\n👋 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'manual':
        manual_arduino_test()
    else:
        test_arduino_connection() 