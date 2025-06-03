#!/usr/bin/env python3
"""
InfluxDB 데이터 직접 확인 스크립트
"""
from influx_storage import influx_manager

def check_influx_temperature_data():
    """InfluxDB에 저장된 온도 데이터를 확인합니다."""
    print("🔍 InfluxDB 온도 데이터 확인...")
    
    if not influx_manager.query_api:
        print("❌ InfluxDB 연결 실패")
        return
    
    try:
        # 최근 온도 데이터 조회
        query = '''
        from(bucket: "smart_greenhouse")
            |> range(start: -2h)
            |> filter(fn: (r) => r._measurement == "sensor_data")
            |> filter(fn: (r) => r.metric == "temperature")
            |> filter(fn: (r) => r._field == "value")
            |> sort(columns: ["_time"])
            |> tail(n: 10)
        '''
        
        result = influx_manager.query_api.query(org="iotctd", query=query)
        
        print("📊 최근 10개 온도 데이터:")
        print("   시간                    | 값     | 모드")
        print("   " + "-" * 45)
        
        values = []
        for table in result:
            for record in table.records:
                timestamp = record.get_time().strftime("%Y-%m-%d %H:%M:%S")
                value = record.get_value()
                mode = record.values.get("mode", "unknown")
                values.append(value)
                print(f"   {timestamp} | {value:6.2f}°C | {mode}")
        
        if values:
            print(f"\n📈 통계:")
            print(f"   최소값: {min(values):.2f}°C")
            print(f"   최대값: {max(values):.2f}°C")
            print(f"   평균값: {sum(values)/len(values):.2f}°C")
            
            # API 응답과 비교
            print(f"\n🔄 API 형식으로 변환된 값들:")
            print(f"   {values}")
        else:
            print("   ⚠️  데이터 없음")
    
    except Exception as e:
        print(f"❌ 쿼리 오류: {e}")

def check_influx_soil_data():
    """InfluxDB에 저장된 토양 습도 데이터를 확인합니다."""
    print("🔍 InfluxDB 토양 습도 데이터 확인...")
    
    if not influx_manager.query_api:
        print("❌ InfluxDB 연결 실패")
        return
    
    try:
        # 최근 토양 습도 데이터 조회
        query = '''
        from(bucket: "smart_greenhouse")
            |> range(start: -2h)
            |> filter(fn: (r) => r._measurement == "sensor_data")
            |> filter(fn: (r) => r.metric == "soil")
            |> filter(fn: (r) => r._field == "value")
            |> sort(columns: ["_time"])
            |> tail(n: 20)
        '''
        
        result = influx_manager.query_api.query(org="iotctd", query=query)
        
        print("📊 최근 20개 토양 습도 데이터:")
        print("   시간                    | 값      | 모드")
        print("   " + "-" * 45)
        
        values = []
        for table in result:
            for record in table.records:
                timestamp = record.get_time().strftime("%Y-%m-%d %H:%M:%S")
                value = record.get_value()
                mode = record.values.get("mode", "unknown")
                values.append(value)
                print(f"   {timestamp} | {value:6.2f}% | {mode}")
        
        if values:
            print(f"\n📈 통계:")
            print(f"   최소값: {min(values):.2f}%")
            print(f"   최대값: {max(values):.2f}%")
            print(f"   평균값: {sum(values)/len(values):.2f}%")
            
            # API 응답과 비교
            print(f"\n🔄 API 형식으로 변환된 값들:")
            print(f"   {values}")
        else:
            print("   ⚠️  데이터 없음")
    
    except Exception as e:
        print(f"❌ 쿼리 오류: {e}")

def check_data_sources():
    """데이터 소스별로 확인합니다."""
    print("\n🎯 데이터 소스별 확인...")
    
    if not influx_manager.query_api:
        return
    
    try:
        # 모드별 데이터 개수 확인
        query = '''
        from(bucket: "smart_greenhouse")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "sensor_data")
            |> filter(fn: (r) => r.metric == "temperature")
            |> group(columns: ["mode"])
            |> count()
        '''
        
        result = influx_manager.query_api.query(org="iotctd", query=query)
        
        print("📊 모드별 데이터 개수:")
        for table in result:
            for record in table.records:
                mode = record.values.get("mode", "unknown")
                count = record.get_value()
                print(f"   {mode:15s}: {count}개")
    
    except Exception as e:
        print(f"❌ 모드별 확인 오류: {e}")

if __name__ == "__main__":
    check_influx_temperature_data()
    check_influx_soil_data()
    check_data_sources() 