#!/usr/bin/env python3
"""
새로운 실시간 데이터 생성 스크립트
"""
import time
from sensors import SensorDataManager

# 센서 매니저 인스턴스 생성
sensor_manager = SensorDataManager()

def generate_fresh_data(count=5):
    """새로운 센서 데이터를 생성합니다."""
    print(f"🔄 새로운 센서 데이터 {count}회 수집...")
    
    for i in range(count):
        try:
            # 센서 값 업데이트
            sensor_manager.update_sensor_values()
            
            # 현재 센서 값 가져오기
            temp = sensor_manager.current_values.get('temperature', 'N/A')
            humidity = sensor_manager.current_values.get('humidity', 'N/A')
            power = sensor_manager.current_values.get('power', 'N/A')
            soil = sensor_manager.current_values.get('soil', 'N/A')
            
            print(f"  {i+1}/{count}: 🌡️{temp}°C, 💧{humidity}%, ⚡{power}W, 🌱{soil}%")
            time.sleep(3)  # 3초 간격
        except Exception as e:
            print(f"  {i+1}/{count}: 오류 - {e}")
    
    print("✅ 새로운 데이터 생성 완료!")
    print("\n🎯 이제 React Native 앱에서 그래프를 확인해보세요:")
    print("1. 앱을 재시작하거나")
    print("2. 온도/습도 카드를 클릭하거나")
    print("3. 🔄 새로고침 버튼을 눌러보세요")

if __name__ == "__main__":
    generate_fresh_data() 