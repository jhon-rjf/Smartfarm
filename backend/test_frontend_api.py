#!/usr/bin/env python3
"""
프론트엔드 API 연결 테스트 스크립트
"""
import requests
import json

def test_frontend_api_calls():
    """프론트엔드에서 호출할 API들을 테스트합니다."""
    print("🧪 프론트엔드 API 연결 테스트")
    print("=" * 50)
    
    base_url = 'http://localhost:5001'
    
    # 1. 상태 API 테스트
    try:
        print("1️⃣ 상태 API 테스트...")
        response = requests.get(f'{base_url}/api/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 온도: {data.get('temperature', 'N/A')}°C")
            print(f"   ✅ 습도: {data.get('humidity', 'N/A')}%")
            print(f"   ✅ 전력: {data.get('power', 'N/A')}W")
            print(f"   ✅ 토양: {data.get('soil', 'N/A')}%")
        else:
            print(f"   ❌ 상태 API 오류: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ 상태 API 오류: {e}")
    
    # 2. 히스토리 API 테스트 (모든 메트릭)
    print("\n2️⃣ 히스토리 API 테스트...")
    metrics = ['temperature', 'humidity', 'power', 'soil']
    
    for metric in metrics:
        try:
            response = requests.get(f'{base_url}/api/history?metric={metric}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    latest_value = data[-1].get('value', 'N/A')
                    print(f"   ✅ {metric:12s}: {len(data):2d}개 포인트, 최신값: {latest_value}")
                else:
                    print(f"   ⚠️  {metric:12s}: 데이터 없음")
            else:
                print(f"   ❌ {metric:12s}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {metric:12s}: {e}")
    
    # 3. 시스템 상태 확인
    print("\n3️⃣ 시스템 상태 확인...")
    try:
        # 아두이노 상태
        response = requests.get(f'{base_url}/api/arduino/status', timeout=5)
        if response.status_code == 200:
            arduino_data = response.json()
            mode = arduino_data.get('mode', 'Unknown')
            connected = arduino_data.get('connected', False)
            print(f"   🔌 아두이노: {mode} ({'연결됨' if connected else '연결 안됨'})")
        
        # InfluxDB 상태
        response = requests.get(f'{base_url}/api/influxdb/status', timeout=5)
        if response.status_code == 200:
            influx_data = response.json()
            connected = influx_data.get('connected', False)
            print(f"   💾 InfluxDB: {'연결됨' if connected else '연결 안됨'}")
        
    except Exception as e:
        print(f"   ❌ 시스템 상태 확인 오류: {e}")

def simulate_react_native_request():
    """React Native 앱의 실제 요청을 시뮬레이션합니다."""
    print("\n🎯 React Native 앱 요청 시뮬레이션")
    print("-" * 50)
    
    base_url = 'http://localhost:5001'
    
    # React Native 앱이 호출하는 순서대로 테스트
    
    # 1. 앱 시작시 상태 데이터 요청
    print("📱 앱 시작: 상태 데이터 요청...")
    try:
        response = requests.get(f'{base_url}/api/status')
        if response.status_code == 200:
            status = response.json()
            print(f"   현재 온도: {status.get('temperature')}°C")
        else:
            print(f"   상태 요청 실패: {response.status_code}")
    except Exception as e:
        print(f"   상태 요청 오류: {e}")
    
    # 2. 온도 카드 클릭시 히스토리 요청
    print("\n🌡️ 온도 카드 클릭: 히스토리 데이터 요청...")
    try:
        response = requests.get(f'{base_url}/api/history?metric=temperature')
        if response.status_code == 200:
            history = response.json()
            if history:
                chart_data = [item['value'] for item in history[-10:]]  # 최근 10개
                print(f"   차트 데이터: {chart_data}")
                print(f"   데이터 포인트: {len(history)}개")
            else:
                print("   ⚠️  히스토리 데이터가 비어있음")
        else:
            print(f"   히스토리 요청 실패: {response.status_code}")
    except Exception as e:
        print(f"   히스토리 요청 오류: {e}")
    
    # 3. 다른 메트릭들도 테스트
    for metric in ['humidity', 'power', 'soil']:
        metric_icons = {'humidity': '💧', 'power': '⚡', 'soil': '🌱'}
        print(f"\n{metric_icons[metric]} {metric} 카드 클릭...")
        try:
            response = requests.get(f'{base_url}/api/history?metric={metric}')
            if response.status_code == 200:
                history = response.json()
                if history:
                    latest = history[-1]['value']
                    print(f"   최신값: {latest}, 포인트 수: {len(history)}")
                else:
                    print("   ⚠️  데이터 없음")
            else:
                print(f"   요청 실패: {response.status_code}")
        except Exception as e:
            print(f"   요청 오류: {e}")

def check_data_freshness():
    """데이터 신선도 확인"""
    print("\n🕐 데이터 신선도 확인")
    print("-" * 50)
    
    try:
        response = requests.get('http://localhost:5001/api/history?metric=temperature')
        if response.status_code == 200:
            data = response.json()
            if data:
                from datetime import datetime
                latest_timestamp = data[-1]['timestamp']
                latest_time = datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
                current_time = datetime.now()
                
                time_diff = (current_time - latest_time.replace(tzinfo=None)).total_seconds()
                
                print(f"   최신 데이터 시간: {latest_timestamp}")
                print(f"   현재 시간과 차이: {time_diff:.0f}초 전")
                
                if time_diff < 300:  # 5분 이내
                    print("   ✅ 데이터가 신선함")
                elif time_diff < 3600:  # 1시간 이내
                    print("   ⚠️  데이터가 약간 오래됨")
                else:
                    print("   ❌ 데이터가 너무 오래됨")
            else:
                print("   ❌ 데이터 없음")
        else:
            print(f"   ❌ 요청 실패: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 데이터 신선도 확인 오류: {e}")

if __name__ == "__main__":
    test_frontend_api_calls()
    simulate_react_native_request()
    check_data_freshness()
    
    print("\n🎯 결론:")
    print("- API URL이 http://localhost:5001로 올바르게 설정되었는지 확인")
    print("- React Native 앱에서 실제 InfluxDB 데이터가 표시되어야 함")
    print("- 더미 데이터는 더 이상 사용되지 않음")
    print("- 데이터가 없으면 '데이터 수집 중' 메시지 표시") 