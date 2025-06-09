"""
스마트 온실 시스템 프롬프트 관리자
YAML 파일에서 프롬프트를 로드하고 관리하는 모듈
"""
import yaml
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class PromptManager:
    """프롬프트 설정을 관리하는 클래스"""
    
    def __init__(self, config_path: str = "prompts.yaml"):
        """
        PromptManager 초기화
        
        Args:
            config_path: YAML 설정 파일 경로
        """
        self.config_path = config_path
        self.config = {}
        self.load_config()
    
    def load_config(self) -> None:
        """YAML 설정 파일을 로드합니다."""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"프롬프트 설정 파일을 찾을 수 없습니다: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
                print(f"[PromptManager] 설정 파일 로드 완료: {self.config_path}")
                
        except Exception as e:
            print(f"[PromptManager] 설정 파일 로드 오류: {str(e)}")
            # 기본 설정으로 폴백
            self.config = self._get_fallback_config()
    
    def reload_config(self) -> None:
        """설정 파일을 다시 로드합니다."""
        print("[PromptManager] 설정 파일 다시 로드 중...")
        self.load_config()
    
    def get_system_config(self) -> Dict[str, Any]:
        """시스템 설정을 반환합니다."""
        return self.config.get('system_config', {
            'model_temperature': 0.7,
            'max_output_tokens': 2048,
            'response_language': 'korean'
        })
    
    def get_action_tag(self, action_key: str) -> str:
        """액션 태그를 반환합니다."""
        action_tags = self.config.get('action_tags', {})
        return action_tags.get(action_key, f'[ACTION_{action_key.upper()}]')
    
    def get_error_message(self, error_key: str) -> str:
        """오류 메시지를 반환합니다."""
        error_messages = self.config.get('error_messages', {})
        return error_messages.get(error_key, '오류가 발생했습니다.')
    
    def get_default_response(self, response_key: str) -> str:
        """기본 응답을 반환합니다."""
        default_responses = self.config.get('default_responses', {})
        return default_responses.get(response_key, '응답을 준비할 수 없습니다.')
    
    def build_chatbot_prompt(self, 
                           temperature: float, 
                           humidity: float, 
                           soil: float, 
                           power: float,
                           co2: float,
                           device_status: Dict[str, bool],
                           user_location: str = "서울",
                           current_time: str = None,
                           conversation_text: str = "",
                           user_message: str = "") -> str:
        """
        챗봇 프롬프트를 동적으로 구성합니다.
        
        Args:
            temperature: 현재 온도
            humidity: 현재 습도
            soil: 현재 토양 습도
            power: 현재 전력 사용량
            co2: 현재 CO2 농도
            device_status: 장치 상태 딕셔너리
            user_location: 사용자 위치
            current_time: 현재 시간
            conversation_text: 이전 대화 내용
            user_message: 사용자 메시지
        
        Returns:
            완성된 프롬프트 문자열
        """
        if current_time is None:
            current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
        
        chatbot_prompts = self.config.get('chatbot_prompts', {})
        context_templates = self.config.get('context_templates', {})
        
        # 프롬프트 구성 요소들
        components = []
        
        # 1. 시스템 역할
        system_role = chatbot_prompts.get('advanced_system', '')
        if system_role:
            components.append(system_role)
        
        # 2. 온실 시스템 정보
        greenhouse_template = context_templates.get('greenhouse_status', '')
        if greenhouse_template:
            greenhouse_info = greenhouse_template.format(
                temperature=temperature,
                humidity=humidity,
                soil=soil,
                power=power,
                co2=co2
            )
            components.append(greenhouse_info)
        
        # 3. 장치 상태
        device_template = context_templates.get('device_status', '')
        if device_template:
            device_info = device_template.format(device_status=device_status)
            components.append(device_info)
        
        # 4. 위치 및 시간 정보
        location_template = context_templates.get('location_time', '')
        if location_template:
            location_info = location_template.format(
                location=user_location,
                current_time=current_time
            )
            components.append(location_info)
        
        # 5. 대화 히스토리 (있는 경우만)
        if conversation_text:
            history_template = context_templates.get('conversation_history', '')
            if history_template:
                history_info = history_template.format(conversation_text=conversation_text)
                components.append(history_info)
        
        # 6. 사용자 메시지
        message_template = context_templates.get('user_message', '')
        if message_template:
            message_info = message_template.format(user_message=user_message)
            components.append(message_info)
        
        # 7. 액션 지침
        action_guidelines = chatbot_prompts.get('action_guidelines', '')
        if action_guidelines:
            components.append(action_guidelines)
        
        # 8. Few-shot 예시 추가
        examples = chatbot_prompts.get('examples', [])
        if examples:
            example_text = "\n\n예시:\n"
            for example in examples:
                example_text += f"- 사용자: \"{example.get('user', '')}\"\n"
                example_text += f"  응답: \"{example.get('bot', '')}\"\n"
            components.append(example_text)
        
        # 9. 상세 지침
        detailed_guidelines = chatbot_prompts.get('detailed_guidelines', '')
        if detailed_guidelines:
            components.append(detailed_guidelines)
        
        # 최종 프롬프트 조합
        final_prompt = "\n\n".join(components)
        
        return final_prompt
    
    def build_image_analysis_prompt(self, 
                                  user_prompt: str = None,
                                  temperature: float = 25.0,
                                  humidity: float = 60.0,
                                  soil: float = 50.0) -> str:
        """
        이미지 분석용 프롬프트를 구성합니다.
        
        Args:
            user_prompt: 사용자가 요청한 분석 프롬프트
            temperature: 현재 온도
            humidity: 현재 습도  
            soil: 현재 토양 습도
        
        Returns:
            완성된 이미지 분석 프롬프트
        """
        image_prompts = self.config.get('image_analysis_prompts', {})
        
        components = []
        
        # 1. 시스템 역할
        system_role = image_prompts.get('system_role', '')
        if system_role:
            components.append(system_role)
        
        # 2. 분석 지침
        analysis_guidelines = image_prompts.get('analysis_guidelines', '')
        if analysis_guidelines:
            components.append(analysis_guidelines)
        
        # 3. 온실 환경 컨텍스트
        greenhouse_context = f"현재 온실 환경 - 온도: {temperature}°C, 습도: {humidity}%, 토양 습도: {soil}%"
        components.append(greenhouse_context)
        
        # 4. 사용자 요청 (기본값 사용 가능)
        if user_prompt is None:
            user_prompt = image_prompts.get('default_prompt', '이 식물의 상태를 분석해주세요.')
        
        components.append(user_prompt)
        
        return "\n\n".join(components)
    
    def get_basic_system_prompt(self) -> str:
        """기본 시스템 프롬프트를 반환합니다."""
        chatbot_prompts = self.config.get('chatbot_prompts', {})
        system_role = chatbot_prompts.get('system_role', '')
        basic_guidelines = chatbot_prompts.get('basic_guidelines', '')
        
        return f"{system_role}\n\n{basic_guidelines}"
    
    def get_image_system_prompt(self) -> str:
        """이미지 분석용 기본 시스템 프롬프트를 반환합니다."""
        image_prompts = self.config.get('image_analysis_prompts', {})
        return image_prompts.get('system_role', '')
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """설정 파일 로드 실패 시 사용할 기본 설정"""
        return {
            'system_config': {
                'model_temperature': 0.7,
                'max_output_tokens': 2048,
                'response_language': 'korean'
            },
            'error_messages': {
                'api_key_missing': '죄송합니다. AI 서비스가 일시적으로 이용할 수 없습니다.',
                'chat_error': '죄송합니다. 응답 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
                'image_error': '이미지 분석 중 오류가 발생했습니다. 다시 시도해주세요.'
            },
            'chatbot_prompts': {
                'system_role': '당신은 스마트 온실 시스템의 AI 도우미입니다.',
                'basic_guidelines': '사용자를 친절하게 도와주세요.'
            }
        }


# 전역 프롬프트 매니저 인스턴스
prompt_manager = PromptManager()

# 편의 함수들
def get_chatbot_prompt(**kwargs) -> str:
    """챗봇 프롬프트 생성 편의 함수"""
    return prompt_manager.build_chatbot_prompt(**kwargs)

def get_image_prompt(**kwargs) -> str:
    """이미지 분석 프롬프트 생성 편의 함수"""
    return prompt_manager.build_image_analysis_prompt(**kwargs)

def get_error_message(error_key: str) -> str:
    """오류 메시지 조회 편의 함수"""
    return prompt_manager.get_error_message(error_key)

def get_system_config() -> Dict[str, Any]:
    """시스템 설정 조회 편의 함수"""
    return prompt_manager.get_system_config()

def reload_prompts() -> None:
    """프롬프트 설정 다시 로드 편의 함수"""
    prompt_manager.reload_config()


if __name__ == "__main__":
    # 테스트 코드
    print("=== 프롬프트 매니저 테스트 ===")
    
    # 기본 설정 테스트
    config = get_system_config()
    print(f"시스템 설정: {config}")
    
    # 챗봇 프롬프트 테스트
    chatbot_prompt = get_chatbot_prompt(
        temperature=25.5,
        humidity=60.0,
        soil=45.0,
        power=120.0,
        co2=400.0,
        device_status={'fan': False, 'light': True, 'water': False, 'window': False},
        user_message="불 켜줘"
    )
    print(f"\n챗봇 프롬프트 길이: {len(chatbot_prompt)} 문자")
    print(f"챗봇 프롬프트 미리보기: {chatbot_prompt[:200]}...")
    
    # 이미지 분석 프롬프트 테스트
    image_prompt = get_image_prompt(user_prompt="이 식물이 건강한가요?")
    print(f"\n이미지 분석 프롬프트 길이: {len(image_prompt)} 문자")
    print(f"이미지 분석 프롬프트: {image_prompt}")
    
    # 오류 메시지 테스트
    error_msg = get_error_message('chat_error')
    print(f"\n오류 메시지: {error_msg}") 