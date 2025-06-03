"""
스마트 온실 시스템의 프론트엔드와 백엔드 API 연동을 위한 유틸리티 함수들
"""
import requests
import json
import os
from dotenv import load_dotenv
import base64
from PIL import Image
import io
from typing import Dict, Any, List, Optional

# 프롬프트 매니저 import 추가
from prompt_manager import prompt_manager, get_system_config

# 환경 변수 로드
load_dotenv()

# Gemini API 키
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def gemini_text_request(prompt: str, temperature: float = None) -> Dict[str, Any]:
    """
    Google Gemini Pro API를 사용하여 텍스트 생성 요청
    
    Args:
        prompt: 입력 프롬프트
        temperature: 출력의 다양성 (0.0-1.0), None이면 설정에서 로드
    
    Returns:
        API 응답 데이터
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("API 키 오류: GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        raise ValueError("API 키가 설정되지 않았습니다.")
    
    print(f"API 키 확인: 길이 {len(api_key)}자, 마지막 4자리: {api_key[-4:]}")
    
    # 업데이트된 Gemini API URL (v1 사용)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    print(f"API 엔드포인트: {url[:70]}...")
    
    # 시스템 설정에서 기본값 가져오기
    system_config = get_system_config()
    if temperature is None:
        temperature = system_config.get('model_temperature', 0.7)
    max_tokens = system_config.get('max_output_tokens', 2048)
    
    # YAML에서 기본 시스템 프롬프트 가져오기
    system_prompt = prompt_manager.get_basic_system_prompt()
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": system_prompt + "\n\n" + prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"API 요청 데이터: 프롬프트 총 길이 {len(system_prompt) + len(prompt)} 문자")
    print(f"API 요청 구성: temperature={temperature}, maxOutputTokens={max_tokens}")
    
    try:
        print("Gemini API 요청 전송 중...")
        response = requests.post(url, headers=headers, json=payload)
        print(f"응답 상태 코드: {response.status_code}, 컨텐츠 타입: {response.headers.get('Content-Type', 'unknown')}")
        
        if response.status_code != 200:
            error_message = f"API 오류 응답: {response.status_code}"
            try:
                error_data = response.json()
                print(f"오류 응답 데이터: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                if 'error' in error_data:
                    error_message += f", 코드: {error_data.get('error', {}).get('code')}, 메시지: {error_data.get('error', {}).get('message')}"
            except Exception as json_error:
                print(f"응답 JSON 파싱 오류: {str(json_error)}")
                print(f"응답 텍스트: {response.text[:200]}...")
            
            response.raise_for_status()
        
        response_json = response.json()
        print(f"API 응답 받음: 키 목록 {list(response_json.keys())}")
        
        return response_json
    except Exception as e:
        import traceback
        print(f"Gemini API 통신 오류: {str(e)}")
        print(f"오류 상세: {traceback.format_exc()}")
        raise

def gemini_image_request(prompt: str, image_data: bytes, temperature: float = None) -> Dict[str, Any]:
    """
    Google Gemini Pro Vision API를 사용하여 이미지 기반 텍스트 생성 요청
    
    Args:
        prompt: 입력 프롬프트
        image_data: 이미지 바이너리 데이터
        temperature: 출력의 다양성 (0.0-1.0), None이면 설정에서 로드
    
    Returns:
        API 응답 데이터
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API 키가 설정되지 않았습니다.")
    
    # 최신 Gemini API URL - gemini-2.0-flash는 멀티모달(텍스트+이미지) 지원
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    # 이미지를 base64로 인코딩
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # 시스템 설정에서 기본값 가져오기
    system_config = get_system_config()
    if temperature is None:
        temperature = system_config.get('model_temperature', 0.7)
    max_tokens = system_config.get('max_output_tokens', 2048)
    
    # YAML에서 이미지 분석용 시스템 프롬프트 가져오기
    system_prompt = prompt_manager.get_image_system_prompt()
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": system_prompt + "\n\n" + prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"이미지 분석 API 요청: {url[:70]}...")
    print(f"이미지 크기: {len(image_data)} bytes, Base64 크기: {len(image_base64)} chars")
    print(f"시스템 프롬프트 길이: {len(system_prompt)} 문자")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"이미지 API 응답 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"이미지 API 오류: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"이미지 API 오류: {str(e)}")
        raise

def extract_text_from_gemini_response(response: Dict[str, Any]) -> str:
    """
    Gemini API 응답에서 텍스트를 추출합니다.
    
    Args:
        response: Gemini API 응답 데이터
    
    Returns:
        생성된 텍스트
    """
    try:
        return response["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        print(f"응답 구문 분석 오류: {e}")
        print(f"응답 데이터: {json.dumps(response, indent=2)}")
        return "응답을 분석할 수 없습니다."