# 🌍 AI 여행 추천 프로그램

여행 날짜를 입력하면 **AI가 국내 여행지를 추천**하고,
**맛집 검색**과 **1일 일정**까지 자동으로 만들어주는 CLI 프로그램입니다.

여러 API(OpenAI + Kakao)를 조합하여 하나의 여행 리포트를 완성합니다.

---

## ✨ 주요 기능

- 📅 **날짜 기반 AI 여행지 추천** — 날씨, 행사/축제, 추천 이유 포함 (JSON 구조화)
- 🍽️ **맛집 검색** — Kakao Local API로 추천 도시의 맛집 5곳 검색
- 🗓️ **1일 일정 자동 생성** — 오전 / 오후 / 저녁 코스 제안
- 💾 **결과 저장** — Markdown 리포트 + 원본 데이터 JSON
- 🛡️ **에러 처리** — API 키 미설정, 파싱 실패(재시도 1회), 맛집 0건 대응

---

## 🛠️ 설치 방법

### 1. 저장소 클론
```bash
git clone (https://github.com/felix203/travel_planner)
cd travel_planner
```

### 2. 필요한 라이브러리 설치
```bash
pip install openai requests python-dotenv
```

### 3. API 키 설정 (.env 파일 생성)

프로젝트 폴더에 `.env` 파일을 만들고 아래처럼 키를 입력하세요:

```
OPENAI_API_KEY=여기에_OpenAI_키_입력
KAKAO_API_KEY=여기에_Kakao_REST_API_키_입력
```

> 🔑 **키 발급처**
> - OpenAI: https://platform.openai.com/api-keys
> - Kakao: https://developers.kakao.com (내 애플리케이션 → REST API 키)

---

## 🚀 사용 방법

```bash
python travel_planner.py -date "2025-07-15"
```

- `-date` : 여행 날짜 (필수, `YYYY-MM-DD` 형식)
- 날짜 형식이 틀리면 안내 메시지를 출력하고 종료됩니다.

---

## 📂 결과물 확인

실행 후 `results/` 폴더에 두 개의 파일이 생성됩니다:

| 파일 | 설명 |
|------|------|
| `results/travel_report_YYYY-MM-DD.md` | 최종 여행 리포트 (사람이 읽는 용도) |
| `results/travel_data_YYYY-MM-DD.json` | 원본 데이터 (추천 결과 + 맛집 + 오류 목록) |

---

## ⚠️ 주의사항 (보안 필수!)

- 🔒 `.env` 파일에는 **API 키가 들어있으므로 절대 GitHub에 올리지 마세요.**
- 🔒 `.gitignore`에 반드시 `.env`를 추가하세요.
- 🔒 API 키가 유출되면 **즉시 재발급**받으세요.
- 🔒 코드, README, 결과 파일 어디에도 실제 키 값을 작성하지 마세요.

---

## 🧰 사용 기술

- **Python 3.10+**
- **OpenAI API** — 여행지 추천 & 리포트 일정 생성
- **Kakao Local API** — 맛집(장소) 검색
- **python-dotenv** — 환경변수(.env) 관리
