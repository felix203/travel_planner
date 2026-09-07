import requests
from config import KAKAO_API_KEY
from openai import OpenAI
from config import OPENAI_API_KEY

# ① OpenAI 클라이언트 생성 (위쪽에!)
client = OpenAI(api_key=OPENAI_API_KEY, base_url="https://copa.codyssey.kr/v1")


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


# ③ AI 여행 추천 함수
def recommend_travel(city, days):
    """AI에게 여행 코스를 추천받는 함수"""
    prompt = f"{city}로 {days} 여행을 갈 거야. 추천 여행 코스와 꼭 가야 할 장소 5곳을 알려줘."
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "너는 친절한 여행 가이드야."},
            {"role": "user", "content": prompt}
        ]
    )
    answer = response.choices[0].message.content
    return answer

if __name__ == "__main__":
    print("=" * 40)
    print("🌍 AI 여행 추천 프로그램")
    print("=" * 40)

    # 사용자 입력받기
    city = input("여행지를 입력하세요 (예: 부산): ")
    days = input("여행 기간을 입력하세요 (예: 2박 3일): ")

    print(f"\n'{city}' {days} 여행을 추천해드릴게요! 잠시만요...\n")

    # AI 추천 실행
    result = recommend_travel(city, days)

    print("🤖 AI 추천 결과:")
    print(result)