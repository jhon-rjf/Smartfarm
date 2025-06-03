#!/usr/bin/env python3
"""
기상청 API 테스트
"""
import os
import requests
from dotenv import load_dotenv
import json

# 환경 변수 로드
load_dotenv()

# API 키 확인
api_key = os.getenv("WEATHER_API_KEY", "")
if not api_key:
    print("API 키가 설정되지 않았습니다.")
    exit(1)

# 마스킹된 키 출력
masked_key = api_key[:4] + "****" + api_key[-4:]
print(f"API 키: {masked_key}")

# API 요청 파라미터
params = {
    "serviceKey": api_key,
    "numOfRows": 10,
    "pageNo": 1,
    # "dataType": "JSON",  # 일단 생략하고 기본 XML로 테스트
    "base_date": "20250520",  # 예제와 동일한 날짜 사용
    "base_time": "0600",      # 예제와 동일한 시간 사용
    "nx": 55,
    "ny": 127
}

# API 요청
WEATHER_API_BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
print(f"요청 URL: {WEATHER_API_BASE_URL}")
print("API 요청 시작...")

try:
    response = requests.get(WEATHER_API_BASE_URL, params=params)
    status_code = response.status_code
    print(f"응답 상태 코드: {status_code}")
    
    # 응답 헤더 출력
    print("\n응답 헤더:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    # 응답 내용 출력
    content = response.text
    print("\n응답 내용 미리보기 (처음 500자):")
    print(content[:500] + "..." if len(content) > 500 else content)
    
    # JSON 파싱 시도
    try:
        if "application/json" in response.headers.get("Content-Type", ""):
            json_data = response.json()
            print("\nJSON 파싱 성공!")
            print(json.dumps(json_data, indent=2, ensure_ascii=False)[:1000] + "...")
        else:
            print("\n응답이 JSON 형식이 아닙니다.")
    except Exception as e:
        print(f"\nJSON 파싱 오류: {e}")
    
except Exception as e:
    print(f"요청 중 오류 발생: {e}") 