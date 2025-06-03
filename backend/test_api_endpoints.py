#!/usr/bin/env python3
"""
API 엔드포인트 테스트 스크립트
"""
import requests
import json

def test_api_endpoints():
    """API 엔드포인트들을 테스트합니다."""
    print("📊 API 엔드포인트 테스트...")
    print("=" * 50)
    
    base_url = 'http://localhost:5001'
    
    # 서버 상태 확인
    try:
        response = requests.get(f'{base_url}/api/status', timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print("✅ 서버 실행 중")
            print(f"   현재 센서 값: 온도={status_data.get('temperature', 'N/A')}°C, 습도={status_data.get('humidity', 'N/A')}%")
        else:
            print(f"❌ 서버 응답 오류: HTTP {response.status_code}")
            return
    except requests.exceptions.ConnectionRefused:
        print(f"🔌 서버가 실행되지 않음 - {base_url}")
        print("   python app.py로 서버를 먼저 실행해주세요.")
        return
    except Exception as e:
        print(f"❌ 서버 연결 오류: {e}")
        return
    
    print("\n📈 히스토리 데이터 API 테스트...")
    print("-" * 50)
    
    # 히스토리 데이터 테스트
    endpoints = ['temperature', 'humidity', 'soil', 'power']
    
    for metric in endpoints:
        try:
            response = requests.get(f'{base_url}/api/history?metric={metric}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {metric:12s}: {len(data):2d}개 데이터 포인트")
                
                if data:
                    # 최근 3개 데이터 표시
                    recent_data = data[-3:]
                    for item in recent_data:
                        print(f"   {item.get('timestamp', 'N/A'):19s}: {item.get('value', 'N/A'):6.1f}")
                else:
                    print(f"   📝 저장된 데이터 없음 (시뮬레이터 데이터 사용 중)")
            else:
                print(f"❌ {metric:12s}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {metric:12s}: {e}")
    
    print("\n🔧 시스템 상태 API 테스트...")
    print("-" * 50)
    
    # 아두이노 상태 확인
    try:
        response = requests.get(f'{base_url}/api/arduino/status', timeout=5)
        if response.status_code == 200:
            arduino_status = response.json()
            print(f"🔌 아두이노: {arduino_status.get('mode', 'Unknown')} 모드")
            if arduino_status.get('connected', False):
                print(f"   포트: {arduino_status.get('port', 'N/A')}")
        else:
            print(f"❌ 아두이노 상태 조회 실패: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 아두이노 상태 조회 오류: {e}")
    
    # InfluxDB 상태 확인
    try:
        response = requests.get(f'{base_url}/api/influxdb/status', timeout=5)
        if response.status_code == 200:
            influxdb_status = response.json()
            print(f"💾 InfluxDB: {'연결됨' if influxdb_status.get('connected', False) else '연결 안됨'}")
            print(f"   URL: {influxdb_status.get('url', 'N/A')}")
            print(f"   Bucket: {influxdb_status.get('bucket', 'N/A')}")
        else:
            print(f"❌ InfluxDB 상태 조회 실패: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ InfluxDB 상태 조회 오류: {e}")

def test_chart_data_format():
    """차트에서 사용할 데이터 형식을 테스트합니다."""
    print("\n📊 차트 데이터 형식 테스트...")
    print("-" * 50)
    
    base_url = 'http://localhost:5001'
    
    try:
        response = requests.get(f'{base_url}/api/history?metric=temperature', timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            print(f"📈 차트용 온도 데이터: {len(data)}개 포인트")
            
            if data:
                print("   데이터 형식 예시:")
                for i, item in enumerate(data[-5:]):  # 최근 5개
                    timestamp = item.get('timestamp', 'N/A')
                    value = item.get('value', 0)
                    print(f"   [{i+1}] {timestamp} → {value}°C")
                
                # React Native Chart Kit 형식으로 변환 테스트
                chart_values = [item.get('value', 0) for item in data[-5:]]
                chart_labels = [item.get('timestamp', '')[-8:-3] for item in data[-5:]]  # HH:MM 형식
                
                print(f"\n   Chart Kit 형식:")
                print(f"   values: {chart_values}")
                print(f"   labels: {chart_labels}")
            else:
                print("   ⚠️  데이터가 없어 차트 표시 불가")
        else:
            print(f"❌ 차트 데이터 조회 실패: HTTP {response.status_code}")
    
    except Exception as e:
        print(f"❌ 차트 데이터 테스트 오류: {e}")

if __name__ == "__main__":
    test_api_endpoints()
    test_chart_data_format()
    
    print("\n🎯 다음 단계:")
    print("1. 브라우저에서 http://localhost:5001/api/history?metric=temperature 직접 확인")
    print("2. React Native 앱에서 그래프 화면 확인")
    print("3. 실시간 데이터 업데이트 확인") 