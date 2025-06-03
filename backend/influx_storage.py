# InfluxDB 임시 비활성화 모듈

def save_chat_message(session_id, message):
    """임시: 메모리에 저장"""
    print(f"[MOCK] 채팅 메시지 저장: {session_id} - {message}")
    pass

def get_chat_history(session_id, limit=5):
    """임시: 빈 기록 반환"""
    print(f"[MOCK] 채팅 기록 조회: {session_id}")
    return []

def cleanup_expired_sessions():
    """임시: 세션 정리 건너뛰기"""
    print("[MOCK] 세션 정리 건너뛰기")
    pass
