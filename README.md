# Smart Greenhouse System

IoT 기반 스마트 온실 관리 시스템입니다. React Native 앱과 Python Flask 백엔드를 통해 온실 환경을 실시간으로 모니터링하고 제어할 수 있습니다.

## 주요 기능

### 환경 모니터링
- 온도, 습도, 토양 습도, 전력 사용량 실시간 측정
- 시계열 데이터 그래프 표시
- InfluxDB 기반 데이터 저장 및 조회

### 장치 제어
- 환풍기, 급수 시스템, 조명, 창문 원격 제어
- 음성 명령을 통한 자연어 제어
- 자동 모드 설정 및 스케줄링

### AI 기반 서비스
- Google Gemini AI 챗봇 통합
- 식물 이미지 분석 및 상태 진단
- 위치 기반 날씨 정보 제공
- Voice-to-Voice 실시간 음성 대화

## 시스템 구성

### 프론트엔드 (React Native/Expo)
- **플랫폼**: iOS, Android 크로스플랫폼
- **주요 라이브러리**: React Navigation, Expo AV, Socket.IO
- **UI 컴포넌트**: 어르신 친화적 대형 UI 지원

### 백엔드 (Python Flask)
- **웹 프레임워크**: Flask 2.3.3
- **데이터베이스**: InfluxDB (시계열 데이터)
- **AI 통합**: Google Gemini API
- **실시간 통신**: Socket.IO

### 하드웨어 연동
- **센서**: DHT22 (온도/습도), 토양 습도 센서, 전력 측정 센서
- **액추에이터**: 릴레이 모듈, 서보 모터, PWM 펌프
- **플랫폼**: Raspberry Pi 5 (Ubuntu 24.04)

## 설치 및 실행

### 사전 요구사항
- Node.js 18 이상
- Python 3.8 이상
- InfluxDB 2.0 이상
- Expo CLI

### 프론트엔드 설치
```bash
npm install
npx expo start
```

### 백엔드 설치
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 환경 변수 설정
`.env` 파일 생성 후 다음 설정:
```
GEMINI_API_KEY=your_gemini_api_key
INFLUXDB_PASSWORD=your_influxdb_password
SECRET_KEY=your_secret_key
```

## API 엔드포인트

### 센서 데이터
- `GET /api/status` - 현재 센서 상태 조회
- `GET /api/history` - 히스토리 데이터 조회

### 장치 제어
- `POST /api/control` - 장치 제어 명령

### AI 서비스
- `POST /api/chat` - 챗봇 대화
- `POST /api/analyze-image` - 이미지 분석

### 날씨 정보
- `GET /api/weather` - 날씨 정보 조회

## 프로젝트 구조

```
├── App.js                 # 메인 앱 컴포넌트
├── screens/               # 화면 컴포넌트
│   ├── ElderlyChatScreen.js
│   ├── ChatbotScreen.js
│   └── VoiceTestScreen.js
├── components/            # 재사용 컴포넌트
│   ├── StatusCards.js
│   ├── DeviceControl.js
│   └── GraphBox.js
├── services/              # API 서비스
│   └── api.js
├── backend/               # 백엔드 서버
│   ├── app.py
│   ├── sensors.py
│   ├── influx_storage.py
│   └── weather_api.py
└── assets/               # 정적 자원
```

