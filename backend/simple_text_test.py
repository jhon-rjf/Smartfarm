"""
간단한 텍스트 기반 AI 대화 테스트 (완전 새 버전)
Google Gemini를 사용한 스마트 온실 제어 테스트
"""
import os
from google import genai
from dotenv import load_dotenv

# 프롬프트 매니저 import
from prompt_manager import prompt_manager
from sensors import simulator

# 환경 변수 로드
load_dotenv()

def get_greenhouse_context():
    """현재 온실 상태를 컨텍스트로 생성"""
    current_values = simulator.current_values
    device_status = simulator.device_status
    
    context = f"""현재 온실 상태:
온도: {current_values['temperature']:.1f}°C | 습도: {current_values['humidity']:.1f}%
토양습도: {current_values['soil']:.1f}% | 전력: {current_values['power']:.1f}W
조명: {'ON' if device_status['light'] else 'OFF'} | 팬: {'ON' if device_status['fan'] else 'OFF'}
급수: {'ON' if device_status['water'] else 'OFF'} | 창문: {'OPEN' if device_status['window'] else 'CLOSE'}"""
    return context

def chat_with_ai(user_input: str) -> str:
    """사용자 입력을 AI에게 전달하고 응답 받기"""
    try:
        # API 키 확인
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "❌ GEMINI_API_KEY가 설정되지 않았습니다."
        
        # Gemini 클라이언트 생성
        client = genai.Client(api_key=api_key)
        
        # 시스템 프롬프트 생성
        base_prompt = prompt_manager.get_basic_system_prompt()
        system_prompt = f"""{base_prompt}

응답 지침:
- 2문장 이내로 간결하게 답변
- 노년층 농업종사자가 이해하기 쉽게 설명  
- 장치 제어 시 액션 태그 포함

{get_greenhouse_context()}"""

        # AI 응답 생성
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[user_input],
            config=genai.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7
            )
        )
        
        return response.text if response.text else "응답을 생성할 수 없습니다."
        
    except Exception as e:
        return f"❌ 오류: {str(e)}"

def main():
    """메인 함수"""
    print("🤖 스마트 온실 AI 채팅 (텍스트 버전)")
    print("=" * 50)
    print("종료: 'quit' 또는 Ctrl+C")
    print("=" * 50)
    
    try:
        while True:
            # 현재 상태 표시
            print(f"\n📊 {get_greenhouse_context()}")
            print("-" * 50)
            
            # 사용자 입력
            user_input = input("\n👤 입력: ").strip()
            
            # 종료 조건
            if user_input.lower() in ['quit', 'exit', '종료', 'q']:
                print("👋 대화를 종료합니다.")
                break
                
            if not user_input:
                print("❌ 빈 입력입니다.")
                continue
            
            # AI 응답
            print("⏳ AI 응답 생성 중...")
            ai_response = chat_with_ai(user_input)
            print(f"🤖 AI: {ai_response}")
            
    except KeyboardInterrupt:
        print("\n👋 Ctrl+C로 종료합니다.")
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    main() 