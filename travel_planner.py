import requests
import os
import argparse
import json
import re
from datetime import datetime
from config import KAKAO_API_KEY
from openai import OpenAI
from config import OPENAI_API_KEY

# ① OpenAI 클라이언트 생성 (위쪽에!)
client = OpenAI(api_key=OPENAI_API_KEY, base_url="https://copa.codyssey.kr/v1")

CITY_ALIAS = {"서울시": "서울", "제주도": "제주", "부산광역시": "부산"}

def normalize_city(city):
    """추천 도시명 정규화 (동의어·접미사 보정)"""
    city = city.strip()
    city = CITY_ALIAS.get(city, city)
    city = re.sub(r"(특별시|광역시|도)$", "", city)
    return city

# ② 지도 검색 (공급자 교체 가능 구조)
class PlaceSearcher:
    """지도 검색 공급자 인터페이스"""
    def search(self, keyword):
        raise NotImplementedError

class KakaoSearcher(PlaceSearcher):
    """Kakao Local API 구현체"""
    def search(self, keyword):
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
        params = {"query": keyword, "size": 5}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()["documents"]
        else:
            print(f"⚠️ 오류 발생: {response.status_code}")
            return []

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

def extract_json(text):
    """LLM 응답에서 JSON만 추출"""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError("JSON 추출 실패")

def recommend_city(date):
    base_prompt = f"""{date}에 국내 여행을 추천해줘.
반드시 아래 JSON 형식으로만 답변해줘.
{{
  "recommended_city": "도시명",
  "weather": "날씨 요약",
  "events": ["행사1", "행사2"],
  "reason": "추천 이유 2~4문장"
}}
"""
    required_keys = {"recommended_city": str, "weather": str,
                     "events": list, "reason": str}

    for attempt in range(2):
        prompt = base_prompt
        if attempt == 1:  # ✅ 재시도 시 프롬프트 강화
            prompt += "\n[중요] 이전 응답 파싱 실패. 설명·코드블록 없이 순수 JSON만 출력하세요."

        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "너는 여행 추천 전문가야. JSON으로만 답해."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content

        try:
            data = extract_json(answer)  # ✅ 정규식 파싱
            for key, expected_type in required_keys.items():
                if key not in data:
                    raise ValueError(f"필수 키 누락: {key}")
                if not isinstance(data[key], expected_type):
                    raise ValueError(f"타입 오류: {key}")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ 응답 검증 실패 (시도 {attempt + 1}/2): {e}")
            if attempt == 0:
                print("   프롬프트를 보정하여 재시도합니다...")

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

def load_previous_errors(path):
    """과거 JSON에서 errors를 읽어 누적"""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("errors", [])
    return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 여행 추천 프로그램")
    parser.add_argument("-date", required=True, help='여행 날짜 (예: -date "2025-07-15")')
    parser.add_argument("--force", action="store_true", help="캐시 무시하고 재실행")  # ✅ #16
    args = parser.parse_args()

    if not validate_date(args.date):
        print("❌ 날짜 형식이 올바르지 않습니다. 예: -date \"2025-07-15\"")
        exit()
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        exit()
    if not KAKAO_API_KEY:
        print("❌ KAKAO_API_KEY가 설정되지 않았습니다.")
        exit()

    json_path = os.path.join("results", f"travel_data_{args.date}.json")

    # ✅ #16 캐시 재사용
    if os.path.exists(json_path) and not args.force:
        print("♻️ 캐시된 결과를 재사용합니다. (새로 실행하려면 --force)")
        with open(json_path, encoding="utf-8") as f:
            cached = json.load(f)
        print(cached["recommendation"])
        exit()

    errors = load_previous_errors(json_path)  # ✅ #9 이전 오류 누적

    try:
        recommendation = recommend_city(args.date)
        print("🤖 AI 추천 결과 (JSON):")
        print(recommendation)

        city = normalize_city(recommendation["recommended_city"])  # ✅ #17 정규화
        print("추천 도시:", city)

        keyword = f"{city} 맛집"
        print(f"\n🍽️ '{keyword}' 검색 결과:")
        searcher = KakaoSearcher()          # ✅ #8 래퍼 사용
        places = searcher.search(keyword)

        if places:
            for i, place in enumerate(places, 1):
                name = place["place_name"]
                address = place.get("road_address_name") or place.get("address_name", "주소 없음")
                print(f"{i}. {name} ({address})")
        else:
            print("데이터 없음")
            errors.append("맛집 검색 결과 0건")

        print("\n🗓️ 1일 일정 생성 중...")
        itinerary = make_itinerary(city, places)
        print(itinerary)

        save_report(args.date, recommendation, places, itinerary, errors)
        save_raw_data(args.date, recommendation, places, errors)

    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {e}")
        errors.append(str(e))