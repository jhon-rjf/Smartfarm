#!/usr/bin/env python3
"""
기상청 날씨 API 테스트 스크립트
"""
import weather_api

def test_weather():
    """날씨 API 테스트 함수"""
    print("날씨 API 테스트 시작...")
    
    # 서울 날씨 조회
    seoul_result = weather_api.get_weather_forecast("서울")
    
    if seoul_result["success"]:
        print("\n[서울 날씨 정보 조회 성공]")
        message = weather_api.format_forecast_message(seoul_result)
        print(message)
    else:
        print(f"\n[서울 날씨 정보 조회 실패]")
        print(f"오류: {seoul_result['error']}")
    
    # 다른 지역 테스트 (부산)
    print("\n다른 지역 테스트 중...")
    busan_result = weather_api.get_weather_forecast("부산")
    
    if busan_result["success"]:
        print("\n[부산 날씨 정보 조회 성공]")
        message = weather_api.format_forecast_message(busan_result)
        print(message)
    else:
        print(f"\n[부산 날씨 정보 조회 실패]")
        print(f"오류: {busan_result['error']}")

if __name__ == "__main__":
    test_weather() 