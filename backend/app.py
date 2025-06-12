from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import time
from datetime import datetime
import io
from PIL import Image
import uuid
from collections import defaultdict
import random
import requests
import threading
import asyncio
import re

# 커스텀 모듈 임포트
from sensors import simulator
from api_integration import gemini_text_request, gemini_image_request, extract_text_from_gemini_response
import influx_storage  # 시계열 DB 모듈 추가
import weather_api  # 날씨 API 모듈 추가
# from voice_chat_server import GeminiVoiceServer  # Voice chat 서버 제거

# 프롬프트 매니저 추가
from prompt_manager import get_chatbot_prompt, get_image_prompt, get_error_message, prompt_manager

# 환경 변수 로드
load_dotenv()

# Gemini API 키 확인
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("경고: GEMINI_API_KEY가 설정되지 않았습니다. 기본 응답을 사용합니다.")

app = Flask(__name__)
CORS(app)  # 모든 오리진에서의 CORS 요청 허용

# 인메모리 세션 관리 (InfluxDB 대안)
sessions = {}

# 세션 ID 생성 함수
def generate_session_id():
    return str(uuid.uuid4())

# 세션 관리 (대화 기록 저장)
# -> InfluxDB 모듈로 대체
SESSION_EXPIRY = 3600  # 세션 만료 시간 (1시간)

# 기본 응답 및 오류 메시지
DEFAULT_RESPONSES = {
    "chat_error": get_error_message("chat_error"),
    "image_error": get_error_message("image_error"),
    "api_key_missing": get_error_message("api_key_missing"),
    "network_error": get_error_message("network_error"),
    "timeout_error": get_error_message("timeout_error")
}

# 만료된 세션 정리 함수
def cleanup_expired_sessions():
    influx_storage.cleanup_expired_sessions()

# 주기적으로 만료된 세션 정리 (10% 확률로 정리 실행)
@app.before_request
def before_request():
    if random.random() < 0.1:  # 10% 확률로 정리 실행 (너무 자주 하지 않도록)
        cleanup_expired_sessions()

@app.route('/api/status', methods=['GET'])
def get_status():
    """현재 온실의 상태 데이터를 반환합니다."""
    # 센서 값 업데이트
    current_values = simulator.update_sensor_values()
    
    return jsonify({
        "temperature": current_values["temperature"],
        "humidity": current_values["humidity"],
        "power": current_values["power"],
        "soil": current_values["soil"],
        "co2": current_values["co2"],
        "light": current_values["light"],
        "devices": simulator.device_status,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """측정 항목의 기록 데이터를 반환합니다."""
    metric = request.args.get('metric', 'temperature')
    if metric not in ["temperature", "humidity", "power", "soil", "co2", "light"]:
        return jsonify({"error": "유효하지 않은 측정 항목입니다."}), 400
    
    # InfluxDB에서 데이터 가져오기 시도
    try:
        from influx_storage import influx_manager
        if influx_manager.query_api:
            # InfluxDB에서 최근 24시간 **하드웨어 데이터만** 조회
            query = f'''
            from(bucket: "smart_greenhouse")
                |> range(start: -24h)
                |> filter(fn: (r) => r._measurement == "sensor_data")
                |> filter(fn: (r) => r.metric == "{metric}")
                |> filter(fn: (r) => r._field == "value")
                |> filter(fn: (r) => r.mode == "hardware")
                |> aggregateWindow(every: 30m, fn: mean, createEmpty: false)
                |> sort(columns: ["_time"])
            '''
            
            result = influx_manager.query_api.query(org="iotctd", query=query)
            
            history = []
            for table in result:
                for record in table.records:
                    history.append({
                        "timestamp": record.get_time().strftime("%Y-%m-%d %H:%M:%S"),
                        "value": round(record.get_value(), 2)
                    })
            
            # InfluxDB에 데이터가 있으면 반환
            if history:
                print(f"[get_history] {metric} 하드웨어 데이터 반환: {len(history)}개")
                return jsonify(history)
            else:
                print(f"[get_history] {metric} 하드웨어 데이터 없음, 시뮬레이터 데이터 사용")
    except Exception as e:
        print(f"InfluxDB 히스토리 조회 오류: {e}")
    
    # InfluxDB 실패 시 시뮬레이터 데이터 사용
    return jsonify(simulator.get_history(metric))

@app.route('/api/control', methods=['POST'])
def control_device():
    """장치 제어 상태를 업데이트합니다."""
    data = request.json
    if not data or "device" not in data or "status" not in data:
        return jsonify({"error": "잘못된 요청 형식입니다."}), 400
        
    device = data["device"]
    status = data["status"]
    
    success = simulator.update_device(device, status)
    if not success:
        return jsonify({"error": f"유효하지 않은 장치입니다: {device}"}), 400
        
    return jsonify({"success": True, "devices": simulator.device_status})

@app.route('/api/arduino/status', methods=['GET'])
def get_arduino_status():
    """아두이노 연결 상태를 확인합니다."""
    status = simulator.get_arduino_status()
    return jsonify(status)

@app.route('/api/arduino/reconnect', methods=['POST'])
def reconnect_arduino():
    """아두이노 재연결을 시도합니다."""
    success = simulator.reconnect_arduino()
    status = simulator.get_arduino_status()
    return jsonify({
        "success": success,
        "message": "아두이노 재연결 성공" if success else "아두이노 재연결 실패",
        "status": status
    })

@app.route('/api/influxdb/status', methods=['GET'])
def get_influxdb_status():
    """InfluxDB 연결 상태를 확인합니다."""
    try:
        from influx_storage import influx_manager
        status = influx_manager.get_status() if hasattr(influx_manager, 'get_status') else {
            "connected": influx_manager.client is not None,
            "url": "http://localhost:8086",
            "org": "iotctd",
            "bucket": "smart_greenhouse"
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({
            "connected": False,
            "error": str(e),
            "url": "http://localhost:8086",
            "org": "iotctd", 
            "bucket": "smart_greenhouse"
        })

@app.route('/api/chat', methods=['POST'])
def chat():
    """사용자와의 채팅을 처리하고 Gemini API를 사용하여 응답을 생성합니다."""
    data = request.get_json()
    actual_user_message = data.get('message', '')
    session_id = data.get('sessionId', 'default')
    user_location = data.get('location', '서울')
    
    if not actual_user_message:
        return jsonify({"response": "메시지를 입력해주세요.", "session_id": session_id})
    
    print(f"사용자 메시지: {actual_user_message}")
    print(f"세션 ID: {session_id}")
    print(f"사용자 위치: {user_location}")
    
    # API 키 확인
    if not GEMINI_API_KEY:
        print("API 키 없음: GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        return jsonify({"response": DEFAULT_RESPONSES["api_key_missing"], "session_id": session_id}), 200
    
    # 사용자 메시지 저장 (InfluxDB)
    user_msg = {"role": "user", "content": actual_user_message}
    influx_storage.save_chat_message(session_id, user_msg)
    
    # 현재 시간
    current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
    
    # 이전 대화 기록 가져오기 (최근 5개)
    try:
        conversation_history = influx_storage.get_chat_history(session_id, limit=5)
        conversation_text = ""
        for msg in conversation_history[:-1]:  # 방금 저장한 메시지 제외
            role_name = "사용자" if msg["role"] == "user" else "봇"
            conversation_text += f"{role_name}: {msg['content']}\n"
    except Exception as e:
        print(f"대화 기록 로드 오류: {str(e)}")
        conversation_text = ""
    
    # 모든 메시지를 Gemini API로 전달 (AI가 판단)
    print("모든 메시지를 Gemini API로 전달")
    
    # PromptManager를 사용하여 고급 프롬프트 구성
    prompt = get_chatbot_prompt(
        temperature=simulator.current_values['temperature'],
        humidity=simulator.current_values['humidity'],
        soil=simulator.current_values['soil'],
        power=simulator.current_values['power'],
        co2=simulator.current_values['co2'],
        device_status=simulator.device_status,
        user_location=user_location,
        current_time=current_time,
        conversation_text=conversation_text,
        user_message=actual_user_message
    )
    
    print("Gemini API 호출 준비...")
    
    try:
        # API 키 마지막 4자리 로깅 (보안상 전체 키는 로깅하지 않음)
        api_key_preview = GEMINI_API_KEY[-4:] if GEMINI_API_KEY else "None"
        print(f"API 키 확인: ...{api_key_preview} (마지막 4자리)")
        
        # 프롬프트 길이 로깅
        print(f"프롬프트 길이: {len(prompt)} 문자")
        
        # Gemini API 호출
        print("Gemini API 호출 시작...")
        response_data = gemini_text_request(prompt)
        print("Gemini API 응답 수신 완료")
        
        # 응답 구조 검사
        print(f"응답 구조: {list(response_data.keys())}")
        if "candidates" in response_data:
            print(f"응답 후보 수: {len(response_data['candidates'])}")
            if len(response_data['candidates']) > 0:
                candidate_keys = response_data['candidates'][0].keys()
                print(f"첫 번째 후보 구조: {list(candidate_keys)}")
                
                if "content" in response_data['candidates'][0]:
                    content_keys = response_data['candidates'][0]["content"].keys()
                    print(f"컨텐츠 구조: {list(content_keys)}")
        
        # 응답 파싱
        text_response = extract_text_from_gemini_response(response_data)
        
        # 응답 데이터 검증
        if not text_response or len(text_response.strip()) == 0:
            print("빈 응답 오류: Gemini API가 빈 응답을 반환했습니다.")
            print(f"응답 데이터: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            return jsonify({"response": DEFAULT_RESPONSES["chat_error"], "session_id": session_id}), 200
            
        print(f"응답 길이: {len(text_response)} 문자")
        print(f"응답 내용 미리보기: {text_response[:100]}...")
        
        # WEATHER_REQUEST 태그 확인 및 처리
        if "[WEATHER_REQUEST]" in text_response:
            try:
                print(f"날씨 정보 요청 태그 감지: {actual_user_message}")
                weather_data = weather_api.get_current_weather(user_location)
                
                if weather_data["success"]:
                    weather_message = weather_api.format_current_weather_message(weather_data)
                    # 기존 응답에서 태그 제거하고 날씨 정보 추가
                    final_response = text_response.replace("[WEATHER_REQUEST]", "").strip()
                    final_response += f"\n\n{weather_message}"
                    text_response = final_response
                    print(f"날씨 정보 추가 완료")
                else:
                    # 날씨 정보 가져오기 실패시 태그만 제거
                    text_response = text_response.replace("[WEATHER_REQUEST]", "").strip()
                    print(f"날씨 정보 가져오기 실패: {weather_data.get('error', '알 수 없는 오류')}")
            except Exception as weather_error:
                print(f"날씨 정보 처리 오류: {str(weather_error)}")
                # 오류 시 태그만 제거
                text_response = text_response.replace("[WEATHER_REQUEST]", "").strip()
        
        # HISTORY_REQUEST 태그 확인 및 처리
        history_pattern = r'\[HISTORY_REQUEST:([^:]+):([^]]+)\]'
        history_matches = re.findall(history_pattern, text_response)
        
        if history_matches:
            try:
                print(f"과거 데이터 요청 태그 감지: {len(history_matches)}개")
                
                for timestamp_str, metric in history_matches:
                    print(f"요청된 과거 데이터: {timestamp_str} - {metric}")
                    
                    # 타임스탬프 파싱
                    try:
                        target_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H:%M:%S")
                        
                        # InfluxDB에서 과거 데이터 조회
                        historical_data = influx_storage.get_historical_sensor_data(
                            target_time=target_time,
                            metric=metric,
                            tolerance_minutes=30
                        )
                        
                        # 태그를 결과로 교체
                        tag_to_replace = f"[HISTORY_REQUEST:{timestamp_str}:{metric}]"
                        
                        if historical_data['success']:
                            replacement_text = historical_data['message']
                            print(f"과거 데이터 조회 성공: {replacement_text}")
                        else:
                            replacement_text = historical_data['message']
                            print(f"과거 데이터 조회 실패: {replacement_text}")
                        
                        text_response = text_response.replace(tag_to_replace, replacement_text)
                        
                    except ValueError as parse_error:
                        print(f"시간 파싱 오류: {timestamp_str} - {str(parse_error)}")
                        tag_to_replace = f"[HISTORY_REQUEST:{timestamp_str}:{metric}]"
                        error_message = f"시간 형식을 인식할 수 없습니다: {timestamp_str}"
                        text_response = text_response.replace(tag_to_replace, error_message)
                        
            except Exception as history_error:
                print(f"과거 데이터 처리 오류: {str(history_error)}")
                # 오류 시 모든 HISTORY_REQUEST 태그 제거
                text_response = re.sub(history_pattern, "데이터 조회 중 오류가 발생했습니다.", text_response)
        
        # 봇 응답 저장 (InfluxDB)
        bot_msg = {"role": "bot", "content": text_response}
        influx_storage.save_chat_message(session_id, bot_msg)
        
        return jsonify({"response": text_response, "session_id": session_id})
        
    except Exception as gemini_error:
        import traceback
        print(f"Gemini API 오류: {str(gemini_error)}")
        print(f"스택 트레이스: {traceback.format_exc()}")
        
        # 모든 로컬 응답 제거하고 오류 메시지만 반환
        return jsonify({"response": DEFAULT_RESPONSES["chat_error"], "session_id": session_id}), 200

@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    """이미지를 분석하고 Gemini API를 사용하여 분석 결과를 반환합니다."""
    if 'image' not in request.files:
        return jsonify({"error": "이미지가 제공되지 않았습니다."}), 400
        
    image_file = request.files['image']
    user_prompt = request.form.get('prompt', '')
    
    try:
        # API 키 확인
        if not GEMINI_API_KEY:
            return jsonify({"analysis": DEFAULT_RESPONSES["api_key_missing"]}), 200
        
        # 이미지 데이터 읽기
        image_data = image_file.read()
        
        # PromptManager를 사용하여 이미지 분석 프롬프트 구성
        if not user_prompt:
            user_prompt = prompt_manager.config.get('image_analysis_prompts', {}).get('default_prompt', '이 이미지의 온실 식물 상태를 분석하고 조언해주세요.')
        
        enriched_prompt = get_image_prompt(
            user_prompt=user_prompt,
            temperature=simulator.current_values['temperature'],
            humidity=simulator.current_values['humidity'],
            soil=simulator.current_values['soil']
        )
        
        try:
            # Gemini API 호출
            response_data = gemini_image_request(enriched_prompt, image_data)
            analysis_text = extract_text_from_gemini_response(response_data)
            
            if not analysis_text or len(analysis_text.strip()) == 0:
                return jsonify({"analysis": "식물 이미지 분석 중 오류가 발생했습니다. 다시 시도해주세요."}), 200
                
            return jsonify({"analysis": analysis_text})
            
        except Exception as api_error:
            print(f"Gemini 이미지 API 오류: {str(api_error)}")
            return jsonify({"analysis": DEFAULT_RESPONSES["image_error"]}), 200
    
    except Exception as e:
        print(f"이미지 분석 처리 중 오류 발생: {str(e)}")
        return jsonify({"error": DEFAULT_RESPONSES["image_error"]}), 500

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """날씨 예보 정보를 제공합니다."""
    region = request.args.get('region', '서울')
    
    # 날씨 정보 조회
    weather_data = weather_api.get_weather_forecast(region)
    
    if not weather_data["success"]:
        return jsonify({
            "success": False,
            "error": weather_data["error"],
            "data": None
        }), 500
    
    return jsonify({
        "success": True,
        "data": {
            "region": region,
            "weather": weather_data["forecast"],
            "formatted_message": weather_api.format_forecast_message(weather_data)
        }
    })

@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    """현재 날씨 실황 정보를 제공합니다."""
    region = request.args.get('region', '서울')
    
    # 현재 날씨 정보 조회
    weather_data = weather_api.get_current_weather(region)
    
    if not weather_data["success"]:
        return jsonify({
            "success": False,
            "error": weather_data["error"],
            "data": None
        }), 500
    
    return jsonify({
        "success": True,
        "data": {
            "region": region,
            "current": weather_data["current"],
            "formatted_message": weather_api.format_current_weather_message(weather_data)
        }
    })

if __name__ == '__main__':
    # Flask 서버 시작
    app.run(debug=True, host='0.0.0.0', port=5001) 