import requests
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
def save_report(date, recommendation, places):
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
    for i, place in enumerate(places, 1):
        md += f"{i}. **{place['place_name']}** ({place['road_address_name']})\n"

    # 파일로 저장
    filename = f"travel_report_{date}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\n✅ 리포트 저장 완료: {filename}")

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
    """AI에게 여행지를 JSON 형식으로 추천받는 함수"""
    prompt = f"""{date}에 국내 여행을 추천해줘.
반드시 아래 JSON 형식으로만 답변해줘. 다른 설명은 절대 붙이지 마.

{{
  "recommended_city": "도시명 (예: 강릉)",
  "weather": "해당 시기 일반적인 날씨 요약",
  "events": ["행사1", "행사2"],
  "reason": "추천 이유 2~4문장"
}}
"""
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "너는 여행 추천 전문가야. JSON으로만 답해."},
            {"role": "user", "content": prompt}
        ]
    )
    answer = response.choices[0].message.content
    
    # 문자열 → 파이썬 딕셔너리로 변환
    data = json.loads(answer)
    return data

if __name__ == "__main__":
    # ① argparse 설정
    parser = argparse.ArgumentParser(description="AI 여행 추천 프로그램")
    parser.add_argument("-date", required=True, help='여행 날짜 (예: -date "2025-07-15")')
    args = parser.parse_args()

    # ② 날짜 검증
    if not validate_date(args.date):
        print("❌ 날짜 형식이 올바르지 않습니다. 예: -date \"2025-07-15\"")
        exit()

        # AI 추천 실행 (JSON)
    recommendation = recommend_city(args.date)

    print("🤖 AI 추천 결과 (JSON):")
    print(recommendation)
    print()
    print("추천 도시:", recommendation["recommended_city"])

        # 추천 도시로 맛집 검색
    city = recommendation["recommended_city"]
    keyword = f"{city} 맛집"
    
    print(f"\n🍽️ '{keyword}' 검색 결과:")
    places = search_place(keyword)
    
    for i, place in enumerate(places, 1):
        name = place["place_name"]
        address = place["road_address_name"]
        print(f"{i}. {name} ({address})")
        # 리포트 저장
    save_report(args.date, recommendation, places)