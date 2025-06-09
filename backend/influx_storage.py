"""
InfluxDB 시계열 데이터베이스 연결 모듈
"""
import os
from datetime import datetime, timedelta, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# InfluxDB 설정
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "P9YXJFSfmaEruB6NgCfwSa2rEV51DQGQH8T53CJwhzkdxKT37rm71CrlXI-Vd_0IVz4mGeo3iv7SHv5pjt6oDg=="
INFLUXDB_ORG = "iotctd"
INFLUXDB_BUCKET = "smart_greenhouse"

class InfluxDBManager:
    """InfluxDB 연결 및 데이터 관리 클래스"""
    
    def __init__(self):
        """InfluxDB 클라이언트 초기화"""
        try:
            self.client = InfluxDBClient(
                url=INFLUXDB_URL,
                token=INFLUXDB_TOKEN,
                org=INFLUXDB_ORG
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logger.info("InfluxDB 연결 성공")
        except Exception as e:
            logger.error(f"InfluxDB 연결 실패: {e}")
            self.client = None
            self.write_api = None
            self.query_api = None
    
    def save_sensor_data(self, sensor_data):
        """센서 데이터를 InfluxDB에 저장"""
        if not self.write_api:
            logger.warning("InfluxDB 연결 없음 - 센서 데이터 저장 건너뜀")
            return False
        
        try:
            points = []
            timestamp = datetime.utcnow()
            
            # 센서 메트릭별로 개별 포인트 생성
            sensor_metrics = ["temperature", "humidity", "power", "soil"]
            device_metrics = ["device_fan", "device_water", "device_light", "device_window"]
            
            for metric, value in sensor_data.items():
                if metric in sensor_metrics:
                    # 센서 데이터는 metric을 tag로, value를 field로 저장
                    point = Point("sensor_data") \
                        .tag("metric", metric) \
                        .tag("mode", sensor_data.get("mode", "unknown")) \
                        .field("value", float(value)) \
                        .time(timestamp, WritePrecision.NS)
                    points.append(point)
                
                elif metric in device_metrics:
                    # 장치 상태는 별도 measurement로 저장
                    device_name = metric.replace("device_", "")
                    point = Point("device_status") \
                        .tag("device", device_name) \
                        .tag("mode", sensor_data.get("mode", "unknown")) \
                        .field("status", int(value)) \
                        .time(timestamp, WritePrecision.NS)
                    points.append(point)
            
            # 배치로 데이터 저장
            if points:
                self.write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
                logger.info(f"센서 데이터 저장 완료: {len(points)}개 포인트")
                return True
            else:
                logger.warning("저장할 데이터 포인트가 없습니다")
                return False
            
        except Exception as e:
            logger.error(f"센서 데이터 저장 실패: {e}")
            return False
    
    def save_chat_message(self, session_id, message):
        """채팅 메시지를 InfluxDB에 저장"""
        if not self.write_api:
            logger.warning("InfluxDB 연결 없음 - 채팅 메시지 저장 건너뜀")
            return False
        
        try:
            point = Point("chat_messages") \
                .tag("session_id", session_id) \
                .tag("role", message.get("role", "unknown")) \
                .field("content", message.get("content", "")) \
                .time(datetime.utcnow(), WritePrecision.NS)
            
            self.write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
            logger.info(f"채팅 메시지 저장: {session_id} - {message.get('role')}")
            return True
            
        except Exception as e:
            logger.error(f"채팅 메시지 저장 실패: {e}")
            return False
    
    def get_chat_history(self, session_id, limit=5):
        """채팅 히스토리 조회"""
        if not self.query_api:
            logger.warning("InfluxDB 연결 없음 - 빈 채팅 히스토리 반환")
            return []
        
        try:
            query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: -24h)
                |> filter(fn: (r) => r._measurement == "chat_messages")
                |> filter(fn: (r) => r.session_id == "{session_id}")
                |> filter(fn: (r) => r._field == "content")
                |> sort(columns: ["_time"])
                |> tail(n: {limit})
            '''
            
            result = self.query_api.query(org=INFLUXDB_ORG, query=query)
            
            history = []
            for table in result:
                for record in table.records:
                    history.append({
                        "role": record.values.get("role", "unknown"),
                        "content": record.get_value(),
                        "timestamp": record.get_time().isoformat()
                    })
            
            logger.info(f"채팅 히스토리 조회: {session_id} - {len(history)}개 메시지")
            return history
            
        except Exception as e:
            logger.error(f"채팅 히스토리 조회 실패: {e}")
            return []
    
    def get_historical_sensor_data(self, target_time, metric, tolerance_minutes=30):
        """특정 시간대의 센서 데이터를 조회합니다.
        
        Args:
            target_time (datetime): 조회할 목표 시간 (한국시간 기준)
            metric (str): 조회할 센서 메트릭 (temperature, humidity, soil, co2, power)
            tolerance_minutes (int): 허용 오차 시간 (분)
        
        Returns:
            dict: 조회 결과 {'success': bool, 'data': value, 'actual_time': datetime, 'message': str}
        """
        if not self.query_api:
            logger.warning("InfluxDB 연결 없음 - 과거 데이터 조회 불가")
            return {
                'success': False,
                'data': None,
                'actual_time': None,
                'message': 'InfluxDB 연결이 없습니다.'
            }
        
        try:
            # 한국시간(UTC+9)을 UTC로 변환 - timezone 정보 추가
            if target_time.tzinfo is None:
                # timezone-naive인 경우 한국시간으로 가정
                korea_tz = timezone(timedelta(hours=9))
                target_time_korea = target_time.replace(tzinfo=korea_tz)
            else:
                target_time_korea = target_time
            
            # UTC로 변환
            target_time_utc = target_time_korea.astimezone(timezone.utc)
            
            # 목표 시간 주변의 데이터 범위 설정 (UTC 기준)
            start_time = target_time_utc - timedelta(minutes=tolerance_minutes)
            end_time = target_time_utc + timedelta(minutes=tolerance_minutes)
            
            logger.info(f"한국시간 {target_time.strftime('%Y-%m-%d %H:%M:%S')} → UTC {target_time_utc.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # InfluxDB 쿼리 구성
            query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: {start_time.strftime("%Y-%m-%dT%H:%M:%SZ")}, 
                         stop: {end_time.strftime("%Y-%m-%dT%H:%M:%SZ")})
                |> filter(fn: (r) => r._measurement == "sensor_data")
                |> filter(fn: (r) => r.metric == "{metric}")
                |> filter(fn: (r) => r.mode == "hardware")
                |> filter(fn: (r) => r._field == "value")
                |> sort(columns: ["_time"])
            '''
            
            result = self.query_api.query(org=INFLUXDB_ORG, query=query)
            
            # 결과 처리
            records = []
            for table in result:
                for record in table.records:
                    # UTC 시간을 한국시간으로 변환
                    utc_time = record.get_time()  # timezone-aware UTC
                    korea_tz = timezone(timedelta(hours=9))
                    korea_time = utc_time.astimezone(korea_tz)
                    # timezone-naive로 변환 (기존 target_time과 호환)
                    korea_time_naive = korea_time.replace(tzinfo=None)
                    
                    records.append({
                        'time': korea_time_naive,
                        'value': record.get_value()
                    })
            
            if not records:
                return {
                    'success': False,
                    'data': None,
                    'actual_time': None,
                    'message': f'{target_time.strftime("%Y-%m-%d %H:%M")} 시점의 {metric} 데이터를 찾을 수 없습니다.'
                }
            
            # 목표 시간에 가장 가까운 데이터 찾기 (한국시간 기준, timezone-naive)
            target_time_naive = target_time.replace(tzinfo=None) if target_time.tzinfo else target_time
            closest_record = min(records, key=lambda x: abs((x['time'] - target_time_naive).total_seconds()))
            
            # 시간 차이 계산 (분 단위)
            time_diff_minutes = abs((closest_record['time'] - target_time_naive).total_seconds()) / 60
            
            # 메트릭 이름을 한국어로 변환
            metric_names = {
                'temperature': '온도',
                'humidity': '습도', 
                'soil': '토양습도',
                'co2': 'CO2',
                'power': '전력사용량'
            }
            metric_korean = metric_names.get(metric, metric)
            
            # 단위 설정
            units = {
                'temperature': '°C',
                'humidity': '%',
                'soil': '%', 
                'co2': 'ppm',
                'power': 'W'
            }
            unit = units.get(metric, '')
            
            logger.info(f"과거 데이터 조회 성공: {metric} = {closest_record['value']}{unit} "
                       f"({closest_record['time'].strftime('%Y-%m-%d %H:%M:%S')} 한국시간)")
            
            return {
                'success': True,
                'data': closest_record['value'],
                'actual_time': closest_record['time'],
                'message': f'{closest_record["time"].strftime("%Y년 %m월 %d일 %H시 %M분")} 시점의 '
                          f'{metric_korean}는 {closest_record["value"]}{unit}였습니다.'
            }
            
        except Exception as e:
            logger.error(f"과거 센서 데이터 조회 실패: {e}")
            return {
                'success': False,
                'data': None,
                'actual_time': None,
                'message': f'데이터 조회 중 오류가 발생했습니다: {str(e)}'
            }
    
    def cleanup_expired_sessions(self):
        """만료된 세션 데이터 정리"""
        try:
            logger.info("세션 정리 수행")
        except Exception as e:
            logger.error(f"세션 정리 실패: {e}")

# 글로벌 인스턴스 생성
influx_manager = InfluxDBManager()

# 기존 함수 호환성 유지
def save_chat_message(session_id, message):
    return influx_manager.save_chat_message(session_id, message)

def get_chat_history(session_id, limit=5):
    return influx_manager.get_chat_history(session_id, limit)

def cleanup_expired_sessions():
    return influx_manager.cleanup_expired_sessions()

def save_sensor_data(sensor_data):
    return influx_manager.save_sensor_data(sensor_data)

def get_historical_sensor_data(target_time, metric, tolerance_minutes=30):
    """특정 시간대의 센서 데이터를 조회합니다."""
    return influx_manager.get_historical_sensor_data(target_time, metric, tolerance_minutes)
