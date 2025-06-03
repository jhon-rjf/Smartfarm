# 스마트 온실 시스템 백엔드

이 백엔드는 스마트 온실 시스템의 프론트엔드와 연동되는 API 서버입니다.

## 기능

- 온도, 습도, 전력 사용량, 토양 습도 데이터 제공 (더미 데이터)
- 장치 제어 API (팬, 물 공급, 조명, 창문)
- 데이터 기록 및 그래프 데이터 제공
- Gemini AI를 활용한 챗봇 기능
- 식물 이미지 분석 기능 (1024x1024 리사이징 후 Gemini AI 활용)

## 설치 및 실행

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
`.env` 파일을 생성하고 다음 내용을 입력하세요:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

3. 서버 실행:
```bash
python app.py
```

서버는 기본적으로 http://localhost:5000 에서 실행됩니다.

## API 엔드포인트

### 상태 데이터 가져오기
- **GET** `/api/status`
- 응답: 온도, 습도, 전력, 토양 습도 및 장치 상태 데이터

### 기록 데이터 가져오기
- **GET** `/api/history?metric=temperature`
- 매개변수: `metric` (temperature, humidity, power, soil 중 하나)
- 응답: 해당 측정 항목의 시계열 데이터

### 장치 제어
- **POST** `/api/control`
- 요청 본문: `{"device": "fan", "status": true}`
- 응답: 업데이트된 장치 상태

### 챗봇
- **POST** `/api/chat`
- 요청 본문: `{"message": "온실에 적합한 온도는 얼마인가요?"}`
- 응답: Gemini AI의 응답

### 이미지 분석
- **POST** `/api/analyze-image`
- 요청: 멀티파트 폼 데이터 (`image` 파일, `prompt` 텍스트)
- 응답: 이미지 분석 결과

## 프론트엔드 연동

이 백엔드는 React Native 프론트엔드와 연동하여 사용할 수 있습니다.
프론트엔드 애플리케이션의 API 통신 URL을 이 서버의 주소로 설정하세요.
