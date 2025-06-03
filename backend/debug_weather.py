#!/usr/bin/env python3
"""
기상청 날씨 API 디버깅 스크립트
"""
import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 기상청 API 설정
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_API_BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

def debug_api_request():
    """API 요청을 디버깅합니다."""
    print("===== 날씨 API 디버깅 =====")
    
    # API 키 확인
    if not WEATHER_API_KEY:
        print("오류: WEATHER_API_KEY가 설정되지 않았습니다.")
        return
    
    # API 키 마스킹 (일부만 표시)
    key_length = len(WEATHER_API_KEY)
    masked_key = WEATHER_API_KEY[:4] + "*" * (key_length - 8) + WEATHER_API_KEY[-4:] if key_length > 8 else "****"
    print(f"API 키: {masked_key} (길이: {key_length}자)")
    
    # 테스트 파라미터 설정
    region = "서울"
    params = {
        "serviceKey": WEATHER_API_KEY,
        "numOfRows": 10,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": "20230601",  # 테스트용 고정 날짜
        "base_time": "0500",      # 테스트용 고정 시간
        "nx": 60,  # 서울 좌표
        "ny": 127
    }
    
    # URL 인코딩
    query_string = urlencode(params)
    url = f"{WEATHER_API_BASE_URL}?{query_string}"
    
    # URL 정보 출력 (API 키 부분 마스킹)
    url_for_display = url.replace(WEATHER_API_KEY, masked_key)
    print(f"\n요청 URL: {url_for_display}")
    
    try:
        print("\nAPI 요청 시작...")
        response = requests.get(url)
        status_code = response.status_code
        print(f"응답 상태 코드: {status_code}")
        
        # 응답 헤더 출력
        print("\n응답 헤더:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        # 응답 내용 출력
        print("\n응답 내용 미리보기 (처음 500자):")
        content = response.text
        print(content[:500] + "..." if len(content) > 500 else content)
        
        # JSON 파싱 시도
        if "application/json" in response.headers.get("Content-Type", ""):
            try:
                json_data = response.json()
                print("\nJSON 파싱 성공!")
                
                # 응답 코드 확인
                response_code = json_data.get("response", {}).get("header", {}).get("resultCode")
                response_msg = json_data.get("response", {}).get("header", {}).get("resultMsg")
                
                print(f"응답 코드: {response_code}")
                print(f"응답 메시지: {response_msg}")
                
                # 항목 수 확인
                items = json_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
                print(f"응답 항목 수: {len(items)}")
            except ValueError as e:
                print(f"\nJSON 파싱 오류: {e}")
        else:
            print("\n응답이 JSON 형식이 아닙니다.")
    
    except Exception as e:
        print(f"\n요청 중 오류 발생: {e}")

if __name__ == "__main__":
    debug_api_request() 