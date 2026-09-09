import requests
import os
import argparse
import json
from datetime import datetime
from config import KAKAO_API_KEY
from openai import OpenAI
from config import OPENAI_API_KEY

# ① OpenAI 클라이언트 생성 (위쪽에!)
client = OpenAI(api_key=OPENAI_API_KEY, base_url="https://copa.codyssey.kr/v1")

def validate_date(date_str):
    """날짜 형식(YYYY-MM-DD) 검증"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

# ⑤ 리포트 생성 & 저장 함수
def save_report(date, recommendation, places, itinerary, errors):  # ✅ errors 추가
    """추천 결과를 마크다운 파일로 저장"""
    city = recommendation["recommended_city"]

    # 마크다운 내용 조립
    md = f"# 🌍 {date} 여행 추천 리포트\n\n"
    md += f"## 📍 추천 도시: {city}\n\n"
    md += f"**날씨:** {recommendation['weather']}\n\n"

    md += "**주요 행사/축제:**\n"
    for event in recommendation["events"]:
        md += f"- {event}\n"
    md += "\n"

    md += f"**추천 이유:** {recommendation['reason']}\n\n"

    md += f"## 🍽️ {city} 맛집 추천\n"
    if places:  # ← 맛집이 있으면
        for i, place in enumerate(places, 1):
            address = place.get("road_address_name") or place.get("address_name", "주소 없음")
            md += f"{i}. **{place['place_name']}** ({address})\n"
    else:  # ← 맛집이 0건이면
        md += "데이터 없음\n"

    # ⭐ 1일 일정 추가!
    md += f"\n## 🗓️ 추천 1일 일정\n\n"
    md += f"{itinerary}\n"

    # ✅ [추가] 오류 요약을 리포트 최하단에 표시
    if errors:
        md += "\n---\n\n## ⚠️ 처리 중 발생한 오류\n\n"
        for err in errors:
            md += f"- {err}\n"
    else:
        md += "\n---\n\n## ✅ 처리 결과\n\n오류 없이 완료되었습니다.\n"

    # results 폴더 생성
    os.makedirs("results", exist_ok=True)

    # 파일로 저장
    filename = os.path.join("results", f"travel_report_{date}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\n✅ 리포트 저장 완료: {filename}")
    
# ⑥ 원본 데이터 JSON 저장 함수
def save_raw_data(date, recommendation, places, errors):
    """추천 + 맛집 + 오류를 원본 JSON으로 저장"""
    # 저장할 데이터 조립
    raw_data = {
        "date": date,
        "recommendation": recommendation,  # 1차 추천 JSON
        "places": places,                  # 맛집 검색 결과 리스트
        "errors": errors                   # 오류 목록 (빈 리스트일 수 있음)
    }

    # results 폴더 생성 (없으면 만듦)
    os.makedirs("results", exist_ok=True)

    # JSON 파일로 저장
    filename = os.path.join("results", f"travel_data_{date}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 원본 데이터 저장 완료: {filename}")

# ② 카카오 검색 함수
def search_place(keyword):
    """카카오 API로 장소를 검색하는 함수"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }
    params = {
        "query": keyword,
        "size": 5
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        places = result["documents"]
        return places
    else:
        print(f"⚠️ 오류 발생: {response.status_code}")
        return []

# ③ AI 여행 추천 함수 (JSON 버전)
def recommend_city(date):
    """AI에게 여행지를 JSON 형식으로 추천받는 함수 (파싱 실패 시 1회 재시도)"""
    prompt = f"""{date}에 국내 여행을 추천해줘.
반드시 아래 JSON 형식으로만 답변해줘. 다른 설명은 절대 붙이지 마.

{{
  "recommended_city": "도시명 (예: 강릉)",
  "weather": "해당 시기 일반적인 날씨 요약",
  "events": ["행사1", "행사2"],
  "reason": "추천 이유 2~4문장"
}}
"""
    # ✅ [추가] 검증할 필수 키와 타입 정의
    required_keys = {
        "recommended_city": str,
        "weather": str,
        "events": list,
        "reason": str
    }

    # 최대 2번 시도 (첫 시도 + 재시도 1회)
    for attempt in range(2):
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "너는 여행 추천 전문가야. JSON으로만 답해."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content

        try:
            data = json.loads(answer)  # 파싱 시도

            # ✅ [추가] 필수 키 존재 + 타입 검증
            for key, expected_type in required_keys.items():
                if key not in data:
                    raise ValueError(f"필수 키 누락: {key}")
                if not isinstance(data[key], expected_type):
                    raise ValueError(f"타입 오류: {key}")

            return data  # 파싱 + 검증 모두 성공하면 반환!

        except (json.JSONDecodeError, ValueError) as e:  # ✅ ValueError도 잡기
            print(f"⚠️ 응답 검증 실패 (시도 {attempt + 1}/2): {e}")
            if attempt == 0:
                print("   재시도합니다...")

    # 2번 다 실패하면 예외 발생
    raise ValueError("JSON 파싱/검증에 2번 실패했습니다.")
# ④ 1일 일정 생성 함수
def make_itinerary(city, places):
    """추천 도시와 맛집을 바탕으로 1일 일정(오전/오후/저녁)을 생성"""
    # 맛집 이름만 뽑아서 문자열로 만들기
    place_names = ", ".join([p["place_name"] for p in places]) if places else "없음"

    prompt = f"""'{city}' 지역으로 당일치기 여행 일정을 짜줘.
참고할 맛집 목록: {place_names}

아래 형식으로 오전/오후/저녁 일정을 간단히 제안해줘. (각 2~3줄)

**오전:** (내용)
**오후:** (내용)
**저녁:** (내용)
"""
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "너는 여행 일정 플래너야."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    # ① argparse 설정
    parser = argparse.ArgumentParser(description="AI 여행 추천 프로그램")
    parser.add_argument("-date", required=True, help='여행 날짜 (예: -date "2025-07-15")')
    args = parser.parse_args()

    # ② 날짜 검증
    if not validate_date(args.date):
        print("❌ 날짜 형식이 올바르지 않습니다. 예: -date \"2025-07-15\"")
        exit()

    # ③ API 키 확인
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        exit()
    if not KAKAO_API_KEY:
        print("❌ KAKAO_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        exit()

    # ④ 메인 실행 (try-except로 감싸기)
    errors = []  # 오류를 모을 빈 리스트

    try:
        # AI 추천 실행 (JSON)
        recommendation = recommend_city(args.date)

        print("🤖 AI 추천 결과 (JSON):")
        print(recommendation)
        print()

        city = recommendation["recommended_city"]
        print("추천 도시:", city)

        # 추천 도시로 맛집 검색
        keyword = f"{city} 맛집"
        print(f"\n🍽️ '{keyword}' 검색 결과:")
        places = search_place(keyword)

        if places:
            for i, place in enumerate(places, 1):
                name = place["place_name"]
                address = place.get("road_address_name") or place.get("address_name", "주소 없음")
                print(f"{i}. {name} ({address})")
        else:
            print("데이터 없음")
            errors.append("맛집 검색 결과 0건")

        # 1일 일정 생성
        print("\n🗓️ 1일 일정 생성 중...")
        itinerary = make_itinerary(city, places)
        print(itinerary)

        # 리포트 저장 (.md)
        save_report(args.date, recommendation, places, itinerary, errors)

        # 원본 데이터 저장 (.json)
        save_raw_data(args.date, recommendation, places, errors)

    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {e}")
        errors.append(str(e))
        print("프로그램을 종료합니다.")