"""
스마트 온실 시스템을 위한 기상청 단기예보 API 연동 모듈
https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15084084
"""
import os
import json
import requests
import datetime
from urllib.parse import urlencode
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# 환경 변수 로드
load_dotenv()

# 기상청 API 설정
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_API_BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
WEATHER_API_ULTRA_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"

# 날씨 아이콘 매핑
WEATHER_ICON_MAP = {
    # 맑음
    "맑음": "☀️",
    # 구름 관련
    "구름많음": "🌥️",
    "흐림": "☁️",
    # 비 관련
    "비": "🌧️",
    "소나기": "🌦️",
    "장마": "🌧️",
    # 눈 관련
    "눈": "❄️",
    "진눈깨비": "🌨️",
    # 천둥번개 관련
    "천둥": "⛈️",
    "번개": "⛈️",
    # 안개 관련
    "안개": "🌫️",
    # 황사 관련
    "황사": "😷",
    # 기타
    "폭염": "🔥",
    "한파": "🥶"
}

# 행정구역별 좌표 (기상청 API에서 사용하는 좌표계)
REGION_GRID = {
    "서울": {"nx": 60, "ny": 127},
    "인천": {"nx": 55, "ny": 124},
    "경기도": {"nx": 60, "ny": 120},
    "강원도": {"nx": 73, "ny": 134},
    "충청북도": {"nx": 69, "ny": 107},
    "충청남도": {"nx": 68, "ny": 100},
    "전라북도": {"nx": 63, "ny": 89},
    "전라남도": {"nx": 51, "ny": 67},
    "경상북도": {"nx": 89, "ny": 91},
    "경상남도": {"nx": 91, "ny": 77},
    "제주도": {"nx": 52, "ny": 38},
    "대전": {"nx": 67, "ny": 100},
    "대구": {"nx": 89, "ny": 90},
    "울산": {"nx": 102, "ny": 84},
    "부산": {"nx": 98, "ny": 76},
    "광주": {"nx": 58, "ny": 74},
}

def check_api_key() -> bool:
    """
    API 키가 설정되어 있는지 확인합니다.
    
    Returns:
        bool: API 키 설정 여부
    """
    if not WEATHER_API_KEY:
        print("날씨 API 키가 설정되지 않았습니다.")
        return False
    return True

def get_forecast_date() -> tuple:
    """
    예보 날짜와 시간을 계산합니다.
    기상청 API는 매시 45분에 업데이트되므로, 현재 시간이 45분 이전이면 1시간 전 데이터를 요청합니다.
    
    Returns:
        tuple: (날짜, 시간) 형식의 튜플
    """
    now = datetime.datetime.now()
    
    # 현재 시간이 45분 이전이면 1시간 전 데이터 사용
    if now.minute < 45:
        now = now - datetime.timedelta(hours=1)
    
    # 시간을 30분 기준으로 가장 최근 발표 시각으로 변경
    if now.hour < 2:
        # 오전 2시 이전은 전날 23시 발표 데이터 사용
        yesterday = now - datetime.timedelta(days=1)
        base_date = yesterday.strftime("%Y%m%d")
        base_time = "2300"
    else:
        hour = now.hour
        base_hour = hour - (hour % 3)  # 3시간 단위로 내림
        base_date = now.strftime("%Y%m%d")
        base_time = f"{base_hour:02d}00"  # 시간 형식을 0200, 0500, 0800 등으로 변환
    
    return (base_date, base_time)

def get_weather_forecast(region_name: str = "서울") -> Dict[str, Any]:
    """
    기상청 단기예보 API를 호출하여 날씨 정보를 가져옵니다.
    
    Args:
        region_name: 지역명 (서울, 인천, 부산 등)
        
    Returns:
        날씨 정보 딕셔너리
    """
    if not check_api_key():
        return {
            "success": False,
            "error": "API 키가 설정되지 않았습니다.",
            "forecast": None
        }
    
    try:
        # 행정구역별 좌표 확인
        if region_name not in REGION_GRID:
            region_name = "서울"  # 기본값으로 서울 사용
        
        grid = REGION_GRID[region_name]
        nx, ny = grid["nx"], grid["ny"]
        
        # 예보 날짜와 시간 계산
        base_date, base_time = get_forecast_date()
        
        # API 요청 파라미터 구성
        params = {
            "serviceKey": WEATHER_API_KEY,
            "numOfRows": 100,
            "pageNo": 1,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny
        }
        
        # API 요청
        query_string = urlencode(params)
        url = f"{WEATHER_API_BASE_URL}?{query_string}"
        
        response = requests.get(url)
        response.raise_for_status()  # HTTP 오류 체크
        
        data = response.json()
        
        # API 응답 확인
        response_code = data.get("response", {}).get("header", {}).get("resultCode")
        
        if response_code != "00":
            error_msg = data.get("response", {}).get("header", {}).get("resultMsg", "알 수 없는 오류")
            return {
                "success": False,
                "error": f"API 오류: {error_msg}",
                "forecast": None
            }
        
        # 예보 항목 추출
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        # 날씨 정보 정리
        forecast_data = parse_forecast_data(items, region_name)
        
        return {
            "success": True,
            "error": None,
            "forecast": forecast_data
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"API 요청 오류: {str(e)}",
            "forecast": None
        }
    except Exception as e:
        import traceback
        print(f"날씨 정보 조회 중 오류: {str(e)}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": f"날씨 정보 처리 오류: {str(e)}",
            "forecast": None
        }

def parse_forecast_data(items: List[Dict[str, Any]], region_name: str) -> Dict[str, Any]:
    """
    기상청 API 응답에서 날씨 정보를 추출하여 정리합니다.
    
    Args:
        items: API 응답 아이템 목록
        region_name: 지역명
        
    Returns:
        정리된 날씨 정보
    """
    # 예보 시간별 데이터 정리
    forecast = {}
    
    for item in items:
        # 예보 시간
        fcst_date = item.get("fcstDate")
        fcst_time = item.get("fcstTime")
        
        # 시간별로 데이터 그룹화
        time_key = f"{fcst_date}_{fcst_time}"
        
        if time_key not in forecast:
            forecast[time_key] = {
                "date": fcst_date,
                "time": fcst_time,
            }
        
        # 예보 항목 분류
        category = item.get("category")
        value = item.get("fcstValue")
        
        # 필요한 항목만 저장
        if category == "POP":  # 강수확률
            forecast[time_key]["precipitation_prob"] = f"{value}%"
        elif category == "PTY":  # 강수형태 (0:없음, 1:비, 2:비/눈, 3:눈, 4:소나기)
            pty_map = {
                "0": "없음",
                "1": "비",
                "2": "비/눈",
                "3": "눈",
                "4": "소나기"
            }
            forecast[time_key]["precipitation_type"] = pty_map.get(value, "알 수 없음")
        elif category == "SKY":  # 하늘상태 (1:맑음, 3:구름많음, 4:흐림)
            sky_map = {
                "1": "맑음",
                "3": "구름많음",
                "4": "흐림"
            }
            forecast[time_key]["sky"] = sky_map.get(value, "알 수 없음")
        elif category == "TMP":  # 1시간 기온
            forecast[time_key]["temperature"] = f"{value}°C"
        elif category == "REH":  # 습도
            forecast[time_key]["humidity"] = f"{value}%"
        elif category == "WSD":  # 풍속
            forecast[time_key]["wind_speed"] = f"{value}m/s"
        elif category == "PCP":  # 1시간 강수량
            forecast[time_key]["precipitation"] = value
    
    # 시간 순으로 정렬
    sorted_forecast = sorted(list(forecast.values()), key=lambda x: (x["date"], x["time"]))
    
    # 현재부터 24시간 예보 선택 (3시간 간격)
    forecast_3hour = []
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    
    for f in sorted_forecast:
        fcst_datetime = f"{f['date']}_{f['time']}"
        
        # 날씨 아이콘 설정
        weather_desc = ""
        if "precipitation_type" in f and f["precipitation_type"] != "없음":
            weather_desc = f["precipitation_type"]
        elif "sky" in f:
            weather_desc = f["sky"]
        
        icon = WEATHER_ICON_MAP.get(weather_desc, "🌈")
        f["icon"] = icon
        
        # 현재 시각 이후의 예보만 선택
        if f["date"] >= current_date:
            forecast_3hour.append(f)
        
        # 최대 8개 항목만 선택 (24시간)
        if len(forecast_3hour) >= 8:
            break
    
    # 요약 정보 생성
    current = forecast_3hour[0] if forecast_3hour else {}
    
    # 강수확률과 날씨 상태 결합하여 요약
    weather_status = ""
    if current.get("sky"):
        weather_status += current.get("sky", "")
    
    if current.get("precipitation_type") and current.get("precipitation_type") != "없음":
        if weather_status:
            weather_status += ", "
        weather_status += current.get("precipitation_type", "")
    
    summary = {
        "region": region_name,
        "current_temp": current.get("temperature", "알 수 없음"),
        "current_humidity": current.get("humidity", "알 수 없음"),
        "precipitation_prob": current.get("precipitation_prob", "0%"),
        "weather_status": weather_status,
        "icon": current.get("icon", "🌈"),
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    return {
        "summary": summary,
        "hourly": forecast_3hour
    }

def format_forecast_message(forecast_data: Dict[str, Any]) -> str:
    """
    날씨 정보를 텍스트 메시지로 포맷팅합니다.
    
    Args:
        forecast_data: 날씨 예보 데이터
        
    Returns:
        포맷팅된 메시지
    """
    if not forecast_data or not forecast_data.get("success") or not forecast_data.get("forecast"):
        return "날씨 정보를 조회할 수 없습니다. 잠시 후 다시 시도해주세요."
    
    forecast = forecast_data["forecast"]
    summary = forecast["summary"]
    hourly = forecast["hourly"][:3]  # 가장 가까운 시간대 3개만 표시
    
    # 요약 메시지 구성
    message = f"""
{summary['icon']} {summary['region']} 날씨 정보 {summary['icon']}

현재 날씨: {summary['weather_status']}
현재 기온: {summary['current_temp']}
현재 습도: {summary['current_humidity']}
강수확률: {summary['precipitation_prob']}

⏰ 시간대별 예보:
"""
    
    # 시간대별 예보 추가
    for i, hour in enumerate(hourly):
        time_str = f"{hour['time'][:2]}시"
        date_str = ""
        
        # 오늘/내일 표시
        today = datetime.datetime.now().strftime("%Y%m%d")
        if hour['date'] != today:
            date_str = " (내일)"
        
        message += f"- {time_str}{date_str}: {hour.get('icon', '')} {hour.get('sky', '알 수 없음')}, {hour.get('temperature', '알 수 없음')}, 강수확률 {hour.get('precipitation_prob', '0%')}\n"
    
    message += f"\n(업데이트: {summary['updated_at']})"
    
    return message.strip()

def get_location_from_message(message: str) -> str:
    """
    메시지에서 위치 정보를 추출합니다.
    
    Args:
        message: 사용자 메시지
        
    Returns:
        추출된 위치 (없으면 '서울' 기본값)
    """
    # 주요 도시 및 지역 목록
    locations = list(REGION_GRID.keys())
    
    # 추가 위치 키워드 (부분적으로 포함된 경우도 인식)
    location_keywords = {
        "서울": ["서울", "수도권", "강남", "강북", "강서", "강동", "여의도"],
        "인천": ["인천", "부평", "송도", "계양", "연수"],
        "부산": ["부산", "해운대", "서면", "광안", "사상", "사하"],
        "대구": ["대구", "동성로", "수성구", "중구", "달서"],
        "광주": ["광주", "충장로", "상무지구"],
        "대전": ["대전", "둔산", "유성", "중앙로"],
        "울산": ["울산", "남구", "북구", "동구", "울주"],
        "경기도": ["경기", "수원", "성남", "고양", "안양", "부천", "안산", "용인"],
        "강원도": ["강원", "춘천", "원주", "강릉", "속초", "동해"],
        "충청북도": ["충북", "청주", "충주", "제천"],
        "충청남도": ["충남", "천안", "아산", "논산", "예산"],
        "전라북도": ["전북", "전주", "익산", "군산", "김제"],
        "전라남도": ["전남", "목포", "순천", "여수", "광양"],
        "경상북도": ["경북", "포항", "경주", "구미", "안동"],
        "경상남도": ["경남", "창원", "진주", "김해", "거제", "통영"],
        "제주도": ["제주", "서귀포", "한라산"]
    }
    
    # 메시지 내 지역명 직접 검색
    for location in locations:
        if location in message:
            return location
    
    # 확장된 키워드로 검색
    for location, keywords in location_keywords.items():
        for keyword in keywords:
            if keyword in message:
                return location
    
    # 기본값으로 서울 반환
    return "서울"

def get_current_weather(region_name: str = "서울") -> Dict[str, Any]:
    """
    기상청 초단기실황 API를 호출하여 현재 날씨 정보를 가져옵니다.
    
    Args:
        region_name: 지역명 (서울, 인천, 부산 등)
        
    Returns:
        현재 날씨 정보 딕셔너리
    """
    if not check_api_key():
        return {
            "success": False,
            "error": "API 키가 설정되지 않았습니다.",
            "current": None
        }
    
    try:
        # 행정구역별 좌표 확인
        if region_name not in REGION_GRID:
            region_name = "서울"  # 기본값으로 서울 사용
        
        grid = REGION_GRID[region_name]
        nx, ny = grid["nx"], grid["ny"]
        
        # 현재 시간 기준으로 API 요청 시간 설정
        now = datetime.datetime.now()
        
        # 현재 분이 45분 이전이면 1시간 전 데이터 사용
        if now.minute < 45:
            now = now - datetime.timedelta(hours=1)
        
        base_date = now.strftime("%Y%m%d")
        base_time = f"{now.hour:02d}00"
        
        # API 요청 파라미터 구성
        params = {
            "serviceKey": WEATHER_API_KEY,
            "numOfRows": 10,
            "pageNo": 1,
            "dataType": "JSON",  # JSON 형식으로 요청
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny
        }
        
        # API 요청
        response = requests.get(WEATHER_API_ULTRA_URL, params=params)
        response.raise_for_status()  # HTTP 오류 체크
        
        # 응답 형식 확인
        content_type = response.headers.get("Content-Type", "")
        
        if "application/json" in content_type:
            data = response.json()
        else:
            # XML 응답인 경우 파싱 시도
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            # XML을 JSON 형식으로 변환
            result_code = root.find(".//resultCode").text
            result_msg = root.find(".//resultMsg").text
            
            if result_code == "00":
                items = []
                for item in root.findall(".//item"):
                    item_dict = {}
                    for child in item:
                        item_dict[child.tag] = child.text
                    items.append(item_dict)
                
                data = {
                    "response": {
                        "header": {
                            "resultCode": result_code,
                            "resultMsg": result_msg
                        },
                        "body": {
                            "items": {
                                "item": items
                            }
                        }
                    }
                }
            else:
                # 오류 응답
                return {
                    "success": False,
                    "error": f"API 오류: {result_msg}",
                    "current": None
                }
        
        # API 응답 확인
        response_code = data.get("response", {}).get("header", {}).get("resultCode")
        
        if response_code != "00":
            error_msg = data.get("response", {}).get("header", {}).get("resultMsg", "알 수 없는 오류")
            return {
                "success": False,
                "error": f"API 오류: {error_msg}",
                "current": None
            }
        
        # 실황 항목 추출
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        # 현재 날씨 정보 정리
        current_data = parse_current_data(items, region_name)
        
        return {
            "success": True,
            "error": None,
            "current": current_data
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"API 요청 오류: {str(e)}",
            "current": None
        }
    except Exception as e:
        import traceback
        print(f"현재 날씨 정보 조회 중 오류: {str(e)}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": f"현재 날씨 정보 처리 오류: {str(e)}",
            "current": None
        }

def parse_current_data(items: List[Dict[str, Any]], region_name: str) -> Dict[str, Any]:
    """
    기상청 초단기실황 API 응답에서 현재 날씨 정보를 추출하여 정리합니다.
    
    Args:
        items: API 응답 아이템 목록
        region_name: 지역명
        
    Returns:
        현재 날씨 정보
    """
    result = {
        "region": region_name,
        "updated_time": "",
        "temperature": None,  # 기온 (T1H)
        "rainfall": None,     # 1시간 강수량 (RN1)
        "humidity": None,     # 습도 (REH)
        "precipitation": None, # 강수형태 (PTY)
        "wind_direction": None, # 풍향 (VEC)
        "wind_speed": None,    # 풍속 (WSD)
    }
    
    # 날씨 코드 매핑
    precipitation_code = {
        "0": "없음",
        "1": "비",
        "2": "비/눈",
        "3": "눈",
        "4": "소나기"
    }
    
    # 기준 시간 정보
    base_date = ""
    base_time = ""
    
    for item in items:
        category = item.get("category")
        value = item.get("obsrValue")
        
        if not base_date and item.get("baseDate"):
            base_date = item.get("baseDate")
        
        if not base_time and item.get("baseTime"):
            base_time = item.get("baseTime")
        
        if category == "T1H":  # 기온
            result["temperature"] = float(value)
        elif category == "RN1":  # 1시간 강수량
            result["rainfall"] = float(value) if value != "강수없음" else 0.0
        elif category == "REH":  # 습도
            result["humidity"] = float(value)
        elif category == "PTY":  # 강수형태
            code = value if value in precipitation_code else "0"
            result["precipitation"] = precipitation_code[code]
        elif category == "VEC":  # 풍향
            result["wind_direction"] = float(value)
        elif category == "WSD":  # 풍속
            result["wind_speed"] = float(value)
    
    # 업데이트 시간 설정
    if base_date and base_time:
        year = base_date[:4]
        month = base_date[4:6]
        day = base_date[6:8]
        hour = base_time[:2]
        minute = base_time[2:4]
        result["updated_time"] = f"{year}-{month}-{day} {hour}:{minute}"
    
    return result

def format_current_weather_message(weather_data: Dict[str, Any]) -> str:
    """
    현재 날씨 정보를 사용자에게 표시할 메시지로 포맷팅합니다.
    
    Args:
        weather_data: 날씨 정보 데이터
        
    Returns:
        포맷팅된 날씨 메시지
    """
    if not weather_data["success"]:
        return f"날씨 정보를 가져오는데 실패했습니다: {weather_data['error']}"
    
    current = weather_data["current"]
    
    if not current:
        return "날씨 정보가 없습니다."
    
    region = current.get("region", "알 수 없음")
    temperature = current.get("temperature", "알 수 없음")
    humidity = current.get("humidity", "알 수 없음")
    rainfall = current.get("rainfall", "알 수 없음")
    precipitation = current.get("precipitation", "알 수 없음")
    wind_speed = current.get("wind_speed", "알 수 없음")
    updated_time = current.get("updated_time", "알 수 없음")
    
    # 날씨 아이콘 추가
    weather_icon = "☁️"  # 기본 아이콘
    
    if precipitation == "비":
        weather_icon = "🌧️"
    elif precipitation == "비/눈":
        weather_icon = "🌨️"
    elif precipitation == "눈":
        weather_icon = "❄️"
    elif precipitation == "소나기":
        weather_icon = "🌦️"
    elif precipitation == "없음" and temperature is not None:
        weather_icon = "☀️"  # 맑음
    
    # 메시지 구성
    message = f"{weather_icon} {region} 현재 날씨 ({updated_time} 기준)\n\n"
    message += f"🌡️ 기온: {temperature}°C\n"
    message += f"💧 습도: {humidity}%\n"
    
    if precipitation != "없음":
        message += f"☔ 강수형태: {precipitation}\n"
        if rainfall is not None and rainfall > 0:
            message += f"🌧️ 강수량: {rainfall}mm\n"
    
    message += f"🌬️ 풍속: {wind_speed}m/s\n"
    
    return message

# API 사용 예시
if __name__ == "__main__":
    # 예시: 서울 날씨 조회
    result = get_weather_forecast("서울")
    
    if result["success"]:
        message = format_forecast_message(result)
        print(message)
    else:
        print(f"날씨 정보 조회 실패: {result['error']}") 