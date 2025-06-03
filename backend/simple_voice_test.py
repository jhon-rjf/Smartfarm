"""
간단한 Voice to Voice 테스트 (로컬 실행)
Google Gemini 2.0 Flash Exp를 사용한 직접 음성 대화
"""
import asyncio
import sounddevice as sd
import numpy as np
from google import genai
import os
from google.genai import types
from dotenv import load_dotenv

# 프롬프트 매니저 import
from prompt_manager import prompt_manager
from sensors import simulator

# 환경 변수 로드
load_dotenv()

# 설정
MODEL = "gemini-2.0-flash-exp"
RATE = 24000
CHANNELS = 1
DTYPE = "int16"

# API 키 확인
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    exit(1)

print(f"✅ Gemini API 키 확인: ...{GEMINI_API_KEY[-4:]}")

# Gemini 클라이언트 초기화
try:
    client = genai.Client(
        api_key=GEMINI_API_KEY, 
        http_options={"api_version": "v1alpha"}
    )
    print("✅ Gemini 클라이언트 초기화 완료")
except Exception as e:
    print(f"❌ Gemini 클라이언트 초기화 실패: {str(e)}")
    exit(1)

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

def play_audio(data: bytes):
    """모델 응답 오디오를 재생하는 함수."""
    try:
        audio_array = np.frombuffer(data, dtype=np.int16)
        print("🔊 AI 응답 재생 중...")
        sd.play(audio_array, samplerate=RATE)
        sd.wait()
        print("✅ 응답 재생 완료")
    except Exception as e:
        print(f"❌ 오디오 재생 오류: {str(e)}")

async def read_audio_stream():
    """마이크 입력을 실시간으로 스트리밍"""
    chunk_duration = 0.5
    frames_per_chunk = int(RATE * chunk_duration)
    silence_threshold = 50  # 무음 임계값 (조정 가능)
    speech_threshold = 100  # 발화 시작 임계값 (조정 가능)
    silence_duration = 2.0  # 무음 지속 시간 (2초)
    chunks_for_silence = int(silence_duration / chunk_duration)
    silent_chunks = 0
    speech_started = False

    print("🎤 마이크에 말씀해 주세요...")
    print("   (발화 감지 후 2초 무음이면 자동 종료)")
    
    with sd.RawInputStream(
        samplerate=RATE, channels=CHANNELS, dtype=DTYPE, blocksize=frames_per_chunk
    ) as stream:
        try:
            while True:
                data, overflowed = stream.read(frames_per_chunk)
                if overflowed:
                    print("!", end="", flush=True)
                else:
                    print(".", end="", flush=True)

                # 음성 크기 계산 (RMS 값 사용)
                audio_data = np.frombuffer(bytes(data), dtype=np.int16)
                rms = np.sqrt(np.mean(np.square(audio_data)))

                # 발화 시작 감지
                if not speech_started and rms > speech_threshold:
                    print("\n🎙️ 발화가 감지되었습니다. 계속 말씀해 주세요...")
                    speech_started = True
                    silent_chunks = 0

                # 발화가 시작된 후에만 무음 감지
                if speech_started:
                    if rms < silence_threshold:
                        silent_chunks += 1
                        if silent_chunks >= chunks_for_silence:
                            print(f"\n⏹️ {silence_duration}초 무음 감지, 녹음 종료")
                            break
                    else:
                        silent_chunks = max(0, silent_chunks - 1)

                yield bytes(data)

        except KeyboardInterrupt:
            print("\n⏹️ 사용자가 중지했습니다.")

async def main():
    """메인 함수 - Gemini Live 세션 실행"""
    
    print("\n🚀 스마트 온실 Voice to Voice 시작!")
    print("="*50)
    
    # Gemini 설정
    config = {
        "generation_config": {
            "response_modalities": ["AUDIO"],
            "temperature": 0.7,
            "candidate_count": 1,
        },
        "system_instruction": get_voice_system_prompt(),
    }
    
    try:
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("✅ Gemini Live 세션 연결 완료")
            
            while True:
                try:
                    print("\n" + "="*50)
                    print("🎙️ 음성 입력을 시작하세요... (Ctrl+C로 전체 종료)")
                    
                    # 실시간 마이크 입력 스트리밍
                    last_chunk = None
                    async for chunk in read_audio_stream():
                        if last_chunk is not None:
                            # 이전 청크는 end_of_turn=False로 전송
                            input_data = types.LiveClientRealtimeInput(
                                media_chunks=[
                                    {"data": last_chunk, "mime_type": "audio/pcm"}
                                ]
                            )
                            await session.send(input_data, end_of_turn=False)
                        last_chunk = chunk

                    if last_chunk is not None:
                        # 마지막 청크를 end_of_turn=True로 전송
                        input_data = types.LiveClientRealtimeInput(
                            media_chunks=[{"data": last_chunk, "mime_type": "audio/pcm"}]
                        )
                        await session.send(input_data, end_of_turn=True)

                        print("⏳ Gemini AI 응답 대기 중...")
                        response_chunks = []
                        async for response in session.receive():
                            if response.data is not None:
                                response_chunks.append(response.data)

                        if response_chunks:
                            complete_audio = b"".join(response_chunks)
                            play_audio(complete_audio)
                        else:
                            print("❌ 응답을 받지 못했습니다.")
                            
                        print("\n💬 계속 대화하시려면 다시 말씀해주세요...")
                        
                except KeyboardInterrupt:
                    print("\n👋 대화를 종료합니다.")
                    break
                except Exception as e:
                    print(f"❌ 오류 발생: {str(e)}")
                    print("🔄 다시 시도해주세요...")
                    
    except Exception as e:
        print(f"❌ Gemini Live 연결 오류: {str(e)}")
        print("\n해결 방법:")
        print("1. GEMINI_API_KEY가 올바른지 확인")
        print("2. 인터넷 연결 상태 확인")
        print("3. Google AI Studio에서 API 키 재발급")

def test_audio_devices():
    """오디오 장치 테스트"""
    print("\n🎵 오디오 장치 테스트")
    print("="*30)
    
    try:
        # 입력 장치 목록
        print("🎤 입력 장치:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  {i}: {device['name']}")
        
        # 출력 장치 목록  
        print("\n🔊 출력 장치:")
        for i, device in enumerate(devices):
            if device['max_output_channels'] > 0:
                print(f"  {i}: {device['name']}")
                
        # 기본 장치 정보
        default_device = sd.query_devices(kind='input')
        print(f"\n기본 입력 장치: {default_device['name']}")
        
        default_device = sd.query_devices(kind='output')
        print(f"기본 출력 장치: {default_device['name']}")
        
    except Exception as e:
        print(f"❌ 오디오 장치 확인 오류: {str(e)}")

if __name__ == "__main__":
    print("🎙️ 스마트 온실 Voice to Voice 테스트")
    print("Google Gemini 2.0 Flash Exp 사용")
    print("="*50)
    
    # 오디오 장치 테스트
    test_audio_devices()
    
    print("\n시작하려면 Enter를 누르세요... (종료: Ctrl+C)")
    try:
        input()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"❌ 실행 오류: {str(e)}")
        import traceback
        print(traceback.format_exc()) 