#!/usr/bin/env python3
"""
InfluxDB 테스트 데이터 생성 스크립트
"""
import time
import random
from datetime import datetime, timedelta
from influx_storage import influx_manager

def generate_test_data(hours=24, interval_minutes=30):
    """
    지정된 시간 동안의 테스트 데이터를 생성합니다.
    
    Args:
        hours: 생성할 데이터의 시간 범위 (기본 24시간)
        interval_minutes: 데이터 포인트 간격 (분 단위, 기본 30분)
    """
    if not influx_manager.write_api:
        print("❌ InfluxDB 연결이 필요합니다!")
        return False
    
    print(f"🔄 {hours}시간 동안의 테스트 데이터 생성 시작...")
    print(f"   간격: {interval_minutes}분")
    
    # 기본 센서 값들
    base_values = {
        'temperature': 25.0,
        'humidity': 60.0,
        'power': 140.0,
        'soil': 45.0
    }
    
    # 변동 범위
    variation_ranges = {
        'temperature': 5.0,  # ±5도
        'humidity': 10.0,    # ±10%
        'power': 20.0,       # ±20W
        'soil': 15.0         # ±15%
    }
    
    # 시간대별 패턴 (온실의 하루 사이클)
    def get_time_factor(hour):
        """시간대에 따른 변동 팩터 반환"""
        if 6 <= hour <= 18:  # 낮시간
            return 1.2  # 온도와 전력 사용량 증가
        else:  # 밤시간
            return 0.8  # 온도와 전력 사용량 감소
    
    total_points = (hours * 60) // interval_minutes
    generated_count = 0
    
    for i in range(total_points):
        # 시간 계산
        timestamp = datetime.now() - timedelta(minutes=i * interval_minutes)
        hour = timestamp.hour
        time_factor = get_time_factor(hour)
        
        # 센서 데이터 생성
        sensor_data = {}
        
        for metric, base_value in base_values.items():
            # 기본 변동
            variation = random.uniform(-variation_ranges[metric], variation_ranges[metric])
            
            # 시간대 패턴 적용 (온도와 전력에만)
            if metric in ['temperature', 'power']:
                value = base_value + (variation * time_factor)
            else:
                value = base_value + variation
            
            # 범위 제한
            if metric == 'temperature':
                value = max(15.0, min(35.0, value))
            elif metric == 'humidity':
                value = max(30.0, min(90.0, value))
            elif metric == 'power':
                value = max(80.0, min(200.0, value))
            elif metric == 'soil':
                value = max(20.0, min(80.0, value))
            
            sensor_data[metric] = round(value, 2)
        
        # 장치 상태도 추가 (랜덤)
        sensor_data.update({
            'device_fan': random.choice([0, 1]),
            'device_water': random.choice([0, 1]),
            'device_light': random.choice([0, 1]),
            'device_window': random.choice([0, 1]),
            'mode': 'simulation'
        })
        
        # InfluxDB에 저장 (시간 지정)
        try:
            from influxdb_client import Point, WritePrecision
            
            points = []
            
            # 센서 데이터 포인트들
            for metric in ['temperature', 'humidity', 'power', 'soil']:
                point = Point("sensor_data") \
                    .tag("metric", metric) \
                    .tag("mode", "simulation") \
                    .field("value", float(sensor_data[metric])) \
                    .time(timestamp, WritePrecision.NS)
                points.append(point)
            
            # 장치 상태 포인트들
            for device in ['fan', 'water', 'light', 'window']:
                point = Point("device_status") \
                    .tag("device", device) \
                    .tag("mode", "simulation") \
                    .field("status", int(sensor_data[f'device_{device}'])) \
                    .time(timestamp, WritePrecision.NS)
                points.append(point)
            
            # 배치 저장
            influx_manager.write_api.write(
                bucket="smart_greenhouse", 
                org="iotctd", 
                record=points
            )
            
            generated_count += 1
            
            # 진행상황 표시
            if generated_count % 10 == 0:
                progress = (generated_count / total_points) * 100
                print(f"   진행률: {progress:.1f}% ({generated_count}/{total_points})")
        
        except Exception as e:
            print(f"❌ 데이터 저장 오류: {e}")
            continue
    
    print(f"✅ 테스트 데이터 생성 완료!")
    print(f"   총 {generated_count}개 시간 포인트 생성")
    print(f"   메트릭별 {generated_count}개 데이터 포인트")
    return True

def verify_generated_data():
    """생성된 데이터를 검증합니다."""
    print("\n🔍 생성된 데이터 검증...")
    
    if not influx_manager.query_api:
        print("❌ InfluxDB 쿼리 API 연결 실패")
        return
    
    metrics = ['temperature', 'humidity', 'power', 'soil']
    
    for metric in metrics:
        try:
            query = f'''
            from(bucket: "smart_greenhouse")
                |> range(start: -25h)
                |> filter(fn: (r) => r._measurement == "sensor_data")
                |> filter(fn: (r) => r.metric == "{metric}")
                |> filter(fn: (r) => r._field == "value")
                |> count()
            '''
            
            result = influx_manager.query_api.query(org="iotctd", query=query)
            
            count = 0
            for table in result:
                for record in table.records:
                    count = record.get_value()
                    break
            
            print(f"   {metric:12s}: {count:3d}개 데이터 포인트")
            
        except Exception as e:
            print(f"   {metric:12s}: 검증 오류 - {e}")

def show_recent_data():
    """최근 데이터를 표시합니다."""
    print("\n📊 최근 데이터 미리보기...")
    
    if not influx_manager.query_api:
        print("❌ InfluxDB 쿼리 API 연결 실패")
        return
    
    try:
        query = '''
        from(bucket: "smart_greenhouse")
            |> range(start: -2h)
            |> filter(fn: (r) => r._measurement == "sensor_data")
            |> filter(fn: (r) => r._field == "value")
            |> sort(columns: ["_time"])
            |> tail(n: 5)
        '''
        
        result = influx_manager.query_api.query(org="iotctd", query=query)
        
        print("   시간                 | 메트릭       | 값")
        print("   " + "-" * 45)
        
        for table in result:
            for record in table.records:
                timestamp = record.get_time().strftime("%Y-%m-%d %H:%M:%S")
                metric = record.values.get("metric", "N/A")
                value = record.get_value()
                print(f"   {timestamp} | {metric:12s} | {value:6.2f}")
        
    except Exception as e:
        print(f"❌ 최근 데이터 조회 오류: {e}")

if __name__ == "__main__":
    print("🧪 InfluxDB 테스트 데이터 생성기")
    print("=" * 50)
    
    # 테스트 데이터 생성 (24시간, 30분 간격 = 48개 포인트)
    if generate_test_data(hours=24, interval_minutes=30):
        
        # 검증
        verify_generated_data()
        
        # 미리보기
        show_recent_data()
        
        print("\n🎯 다음 단계:")
        print("1. React Native 앱에서 그래프 확인")
        print("2. 브라우저에서 http://localhost:5001/api/history?metric=temperature 확인")
        print("3. InfluxDB UI에서 http://localhost:8086 확인")
    else:
        print("❌ 테스트 데이터 생성 실패") 