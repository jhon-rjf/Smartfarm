#!/usr/bin/env python3
"""
InfluxDB 데이터 저장 및 조회 테스트 스크립트
"""
import time
from sensors import simulator
from influx_storage import influx_manager

def test_data_collection():
    """데이터 수집 및 저장 테스트"""
    print("📊 InfluxDB 데이터 수집 테스트 시작...")
    print("=" * 60)
    
    # InfluxDB 연결 상태 확인
    if influx_manager.client:
        print("✅ InfluxDB 연결 성공")
    else:
        print("❌ InfluxDB 연결 실패")
        return
    
    # 아두이노 연결 상태 확인
    arduino_status = simulator.get_arduino_status()
    print(f"🔌 아두이노 상태: {arduino_status}")
    
    print("\n📈 센서 데이터 수집 및 저장 테스트...")
    print("시간 | 온도 | 습도 | 토양 | 전력 | 모드")
    print("-" * 60)
    
    for i in range(10):
        # 센서 데이터 업데이트 (자동으로 InfluxDB에 저장됨)
        values = simulator.update_sensor_values()
        
        mode = "하드웨어" if arduino_status['connected'] else "시뮬레이션"
        
        print(f"{i+1:2d}   | {values['temperature']:4.1f} | {values['humidity']:4.1f} | {values['soil']:4.1f} | {values['power']:6.1f} | {mode}")
        
        time.sleep(2)
    
    print("\n🔍 InfluxDB에서 저장된 데이터 조회...")
    
    # 최근 데이터 조회 테스트
    for metric in ['temperature', 'humidity', 'soil', 'power']:
        try:
            query = f'''
            from(bucket: "smart_greenhouse")
                |> range(start: -1h)
                |> filter(fn: (r) => r._measurement == "sensor_data")
                |> filter(fn: (r) => r.metric == "{metric}")
                |> filter(fn: (r) => r._field == "value")
                |> sort(columns: ["_time"], desc: true)
                |> limit(n: 5)
            '''
            
            result = influx_manager.query_api.query(org="iotctd", query=query)
            
            data_count = 0
            latest_value = None
            
            for table in result:
                for record in table.records:
                    data_count += 1
                    if latest_value is None:
                        latest_value = record.get_value()
            
            print(f"  📊 {metric:12s}: {data_count:2d}개 데이터, 최신값: {latest_value:6.1f}" if latest_value else f"  📊 {metric:12s}: 데이터 없음")
            
        except Exception as e:
            print(f"  ❌ {metric:12s}: 조회 오류 - {e}")
    
    print("\n✅ 데이터 수집 테스트 완료!")

def test_chart_data():
    """차트용 데이터 조회 테스트"""
    print("\n📊 차트 데이터 조회 테스트...")
    print("=" * 60)
    
    for metric in ['temperature', 'humidity', 'soil', 'power']:
        try:
            # 1시간 단위로 집계된 데이터 조회
            query = f'''
            from(bucket: "smart_greenhouse")
                |> range(start: -24h)
                |> filter(fn: (r) => r._measurement == "sensor_data")
                |> filter(fn: (r) => r.metric == "{metric}")
                |> filter(fn: (r) => r._field == "value")
                |> aggregateWindow(every: 10m, fn: mean, createEmpty: false)
                |> sort(columns: ["_time"])
            '''
            
            result = influx_manager.query_api.query(org="iotctd", query=query)
            
            chart_data = []
            for table in result:
                for record in table.records:
                    chart_data.append({
                        "timestamp": record.get_time().strftime("%H:%M"),
                        "value": round(record.get_value(), 1)
                    })
            
            print(f"📈 {metric:12s}: {len(chart_data):2d}개 포인트")
            
            # 최근 5개 데이터 포인트 표시
            if chart_data:
                print(f"   최근 데이터: {chart_data[-5:]}")
            
        except Exception as e:
            print(f"❌ {metric:12s}: 차트 데이터 조회 오류 - {e}")

def test_device_status():
    """장치 상태 데이터 조회 테스트"""
    print("\n🎛️  장치 상태 데이터 조회 테스트...")
    print("=" * 60)
    
    try:
        query = '''
        from(bucket: "smart_greenhouse")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "sensor_data")
            |> filter(fn: (r) => r._field == "value")
            |> filter(fn: (r) => r.metric =~ /device_.*/)
            |> sort(columns: ["_time"], desc: true)
            |> limit(n: 10)
        '''
        
        result = influx_manager.query_api.query(org="iotctd", query=query)
        
        device_data = {}
        for table in result:
            for record in table.records:
                metric = record.values.get("metric", "unknown")
                device_data[metric] = "ON" if record.get_value() == 1 else "OFF"
        
        print("장치 상태:")
        for device, status in device_data.items():
            device_name = device.replace("device_", "").upper()
            print(f"  🎛️  {device_name:8s}: {status}")
        
        if not device_data:
            print("  📝 저장된 장치 상태 데이터 없음")
    
    except Exception as e:
        print(f"❌ 장치 상태 조회 오류: {e}")

if __name__ == "__main__":
    test_data_collection()
    test_chart_data()
    test_device_status()
    
    print("\n🎯 요약:")
    print("- 센서 데이터가 2초마다 InfluxDB에 저장됨")
    print("- 웹 UI에서 /api/history?metric=temperature로 데이터 조회 가능")
    print("- 실시간 그래프에 실제 저장된 데이터 표시됨")
    print("- http://localhost:8086에서 InfluxDB UI 접속 가능") 