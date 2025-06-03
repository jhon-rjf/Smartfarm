"""
스마트 온실 시스템 Voice to Voice 기능
Google Gemini 2.0 Flash Exp를 사용한 실시간 음성 대화
"""
import asyncio
import os
import numpy as np
from google import genai
from google.genai import types
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
import json
import base64
import logging
from dotenv import load_dotenv

# 프롬프트 매니저 import
from prompt_manager import prompt_manager
from sensors import simulator

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 앱 설정
app = Flask(__name__)
app.config['SECRET_KEY'] = 'voice_to_voice_secret'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Gemini 설정
MODEL = "gemini-2.0-flash-exp"
RATE = 24000
CHANNELS = 1
DTYPE = "int16"

# API 키 확인
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    raise ValueError("GEMINI_API_KEY가 필요합니다.")

# Gemini 클라이언트 초기화
try:
    client = genai.Client(
        api_key=GEMINI_API_KEY, 
        http_options={"api_version": "v1alpha"}
    )
    logger.info("Gemini 클라이언트 초기화 완료")
except Exception as e:
    logger.error(f"Gemini 클라이언트 초기화 실패: {str(e)}")
    client = None

def get_greenhouse_context():
    """현재 온실 상태를 컨텍스트로 생성"""
    current_values = simulator.current_values
    device_status = simulator.device_status
    
    context = f"""
    현재 온실 시스템 상태:
    - 온도: {current_values['temperature']:.1f}°C
    - 습도: {current_values['humidity']:.1f}%
    - 토양 습도: {current_values['soil']:.1f}%
    - 전력 사용량: {current_values['power']:.1f}W
    
    장치 상태:
    - 조명: {'켜짐' if device_status['light'] else '꺼짐'}
    - 팬: {'켜짐' if device_status['fan'] else '꺼짐'}
    - 급수: {'켜짐' if device_status['water'] else '꺼짐'}
    - 창문: {'열림' if device_status['window'] else '닫힘'}
    """
    return context

def get_voice_system_prompt():
    """음성 대화용 시스템 프롬프트 생성"""
    # 기본 시스템 프롬프트에서 이모지 제거하고 음성 최적화
    base_prompt = prompt_manager.get_basic_system_prompt()
    
    voice_prompt = f"""{base_prompt}

음성 대화 특별 지침:
1. 응답은 2-3문장 이내로 간결하게 해주세요.
2. 노년층 농업 종사자가 이해하기 쉽게 설명해주세요.
3. 기술적 용어보다는 일상적인 말로 설명해주세요.
4. 장치 제어 요청 시 액션 태그도 함께 말해주세요.
5. 친근하고 다정한 톤으로 대화해주세요.

{get_greenhouse_context()}
"""
    return voice_prompt

# 활성 세션 관리
active_sessions = {}

class VoiceSession:
    """음성 대화 세션 관리 클래스"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.gemini_session = None
        self.is_connected = False
        self.audio_buffer = []
        
    async def connect_gemini(self):
        """Gemini Live 세션 연결"""
        try:
            config = {
                "generation_config": {
                    "response_modalities": ["AUDIO"],
                    "temperature": 0.7,
                    "candidate_count": 1,
                },
                "system_instruction": get_voice_system_prompt(),
            }
            
            self.gemini_session = await client.aio.live.connect(
                model=MODEL, config=config
            )
            self.is_connected = True
            logger.info(f"세션 {self.session_id}: Gemini Live 연결 완료")
            return True
            
        except Exception as e:
            logger.error(f"세션 {self.session_id}: Gemini 연결 실패 - {str(e)}")
            return False
    
    async def send_audio(self, audio_data, end_of_turn=False):
        """오디오 데이터를 Gemini로 전송"""
        if not self.is_connected or not self.gemini_session:
            return False
            
        try:
            input_data = types.LiveClientRealtimeInput(
                media_chunks=[{"data": audio_data, "mime_type": "audio/pcm"}]
            )
            await self.gemini_session.send(input_data, end_of_turn=end_of_turn)
            return True
            
        except Exception as e:
            logger.error(f"세션 {self.session_id}: 오디오 전송 실패 - {str(e)}")
            return False
    
    async def receive_response(self):
        """Gemini 응답 수신"""
        if not self.is_connected or not self.gemini_session:
            return None
            
        try:
            response_chunks = []
            async for response in self.gemini_session.receive():
                if response.data is not None:
                    response_chunks.append(response.data)
            
            if response_chunks:
                complete_audio = b"".join(response_chunks)
                return complete_audio
            return None
            
        except Exception as e:
            logger.error(f"세션 {self.session_id}: 응답 수신 실패 - {str(e)}")
            return None
    
    async def disconnect(self):
        """세션 연결 해제"""
        try:
            if self.gemini_session:
                await self.gemini_session.disconnect()
            self.is_connected = False
            logger.info(f"세션 {self.session_id}: 연결 해제 완료")
        except Exception as e:
            logger.error(f"세션 {self.session_id}: 연결 해제 실패 - {str(e)}")

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    logger.info(f"클라이언트 연결됨: {request.sid}")
    emit('connected', {'status': 'connected', 'session_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    session_id = request.sid
    logger.info(f"클라이언트 연결 해제: {session_id}")
    
    # 활성 세션 정리
    if session_id in active_sessions:
        session = active_sessions[session_id]
        # 비동기 함수를 동기적으로 실행
        try:
            asyncio.run(session.disconnect())
        except Exception as e:
            logger.error(f"세션 정리 오류: {str(e)}")
        
        del active_sessions[session_id]

@socketio.on('start_voice_session')
def handle_start_voice_session():
    """음성 세션 시작"""
    session_id = request.sid
    logger.info(f"음성 세션 시작 요청: {session_id}")
    
    if not client:
        emit('voice_error', {'error': 'Gemini 클라이언트를 사용할 수 없습니다.'})
        return
    
    try:
        # 새 세션 생성
        voice_session = VoiceSession(session_id)
        active_sessions[session_id] = voice_session
        
        # 비동기 연결 작업
        async def connect_session():
            success = await voice_session.connect_gemini()
            if success:
                socketio.emit('voice_session_ready', 
                            {'status': 'ready'}, 
                            room=session_id)
            else:
                socketio.emit('voice_error', 
                            {'error': 'Gemini Live 연결 실패'}, 
                            room=session_id)
        
        # 새 이벤트 루프에서 실행
        asyncio.run(connect_session())
        
    except Exception as e:
        logger.error(f"음성 세션 시작 오류: {str(e)}")
        emit('voice_error', {'error': f'음성 세션 시작 실패: {str(e)}'})

@socketio.on('send_audio_chunk')
def handle_audio_chunk(data):
    """오디오 청크 수신 및 처리"""
    session_id = request.sid
    
    if session_id not in active_sessions:
        emit('voice_error', {'error': '활성 음성 세션이 없습니다.'})
        return
    
    session = active_sessions[session_id]
    
    try:
        # Base64 디코딩
        audio_data = base64.b64decode(data['audio_data'])
        is_final = data.get('is_final', False)
        
        # 비동기 오디오 전송
        async def send_audio_async():
            success = await session.send_audio(audio_data, end_of_turn=is_final)
            
            if is_final and success:
                # 응답 수신
                response_audio = await session.receive_response()
                if response_audio:
                    # Base64 인코딩하여 전송
                    encoded_audio = base64.b64encode(response_audio).decode('utf-8')
                    socketio.emit('voice_response', 
                                {'audio_data': encoded_audio}, 
                                room=session_id)
                else:
                    socketio.emit('voice_error', 
                                {'error': '응답을 받지 못했습니다.'}, 
                                room=session_id)
        
        # 새 이벤트 루프에서 실행
        asyncio.run(send_audio_async())
        
    except Exception as e:
        logger.error(f"오디오 처리 오류: {str(e)}")
        emit('voice_error', {'error': f'오디오 처리 실패: {str(e)}'})

@app.route('/api/voice/status', methods=['GET'])
def voice_status():
    """Voice to Voice 기능 상태 확인"""
    return jsonify({
        'available': client is not None,
        'model': MODEL,
        'active_sessions': len(active_sessions),
        'gemini_api_key_configured': bool(GEMINI_API_KEY)
    })

@app.route('/api/voice/test', methods=['POST'])
def voice_test():
    """Voice to Voice 기능 테스트"""
    if not client:
        return jsonify({'error': 'Gemini 클라이언트를 사용할 수 없습니다.'}), 500
    
    return jsonify({
        'status': 'Voice to Voice 기능이 정상적으로 작동합니다.',
        'model': MODEL,
        'greenhouse_context': get_greenhouse_context()
    })

if __name__ == '__main__':
    print("🎙️ Voice to Voice 서버 시작")
    print(f"모델: {MODEL}")
    print(f"Gemini API 키 설정됨: {bool(GEMINI_API_KEY)}")
    print(f"포트: 5002")
    
    socketio.run(app, host='0.0.0.0', port=5002, debug=True) 