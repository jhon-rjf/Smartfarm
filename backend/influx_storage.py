"""
InfluxDB 시계열 데이터베이스 연결 모듈
"""
import os
from datetime import datetime, timedelta
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
