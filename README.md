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

## 📁 프로젝트 구조

```
travel_planner/
├── travel_planner.py      # 메인 실행 파일
├── config.py              # API 키 로드 (.env 읽기)
├── requirements.txt       # 의존성 목록
├── .env                   # API 키 (git 제외, 직접 생성)
├── .gitignore             # .env 등 제외 설정
├── README.md              # 프로젝트 설명
└── results/               # 실행 결과 저장 폴더 (md + json)
```

### 🔄 프로그램 흐름 (모듈 경계)

```
[날짜 입력] → [AI 추천(JSON)] → [도시 추출] → [맛집 검색] → [일정 생성] → [리포트 저장]
```

| 단계 | 담당 함수 | 역할 |
|------|-----------|------|
| 입력 검증 | `validate_date()` | 날짜 형식(YYYY-MM-DD) 확인 |
| 추천 | `recommend_city()` | LLM 호출 → JSON 파싱·검증 |
| 검색 | `KaKaoSearcher.search()` | Kakao Local API 맛집 조회 |
| 일정 | `make_itinerary()` | 오전/오후/저녁 코스 생성 |
| 저장 | `save_report()/save_raw_data()` | md + json 파일 생성 |

---

## 🛠️ 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/felix203/travel_planner
cd travel_planner
```

### 2. 필요한 라이브러리 설치
```bash
pip install -r requirements.txt
```
> 또는 직접 설치: `pip install openai requests python-dotenv`

### 3. API 키 설정 (.env 파일 생성)

프로젝트 폴더에 `.env` 파일을 만들고 아래처럼 키를 입력하세요:

```
OPENAI_API_KEY=여기에_OpenAI_키_입력
KAKAO_REST_API_KEY=여기에_Kakao_REST_API_키_입력
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

### ⚠️ 날짜 검증 실패 시 출력 예시
```bash
$ python travel_planner.py -date "2025/07/15"
❌ 날짜 형식이 올바르지 않습니다. 예:-date "2025-07-15"
```

### 실행 예시 (정상)
```bash
$ python travel_planner.py -date "2025-07-15"

🤖 AI 추천 결과 (JSON):
{'recommended_city': '보령', 'weather': '7월 중순은 전형적인 한여름으로...',
 'events': ['보령머드축제', '대천해수욕장 해변축제'], 'reason': '보령은 7월에...'}

추천 도시: 보령

🍽️ '보령 맛집' 검색 결과:
1. 오천항 수산물판매센터 8호점 (충남 보령시 오천면 오천해안로 782-5)
2. 피자파티 (충남 보령시 대흥로 44)
...

📅 1일 일정 생성 중...
**오전:** ...
**오후:** ...
**저녁:** ...

✅ 리포트 저장 완료: results\travel_report_2025-07-15.md
✅ 원본 데이터 저장 완료: results\travel_data_2025-07-15.json
```

---

## 📂 결과물 확인

실행 후 `results/` 폴더에 두 개의 파일이 생성됩니다:

| 파일 | 설명 |
|------|------|
| `results/travel_report_YYYY-MM-DD.md` | 최종 여행 리포트 (사람이 읽는 용도) |
| `results/travel_data_YYYY-MM-DD.json` | 원본 데이터 (추천 결과 + 맛집 + 오류 목록) |

### 📛 파일 네이밍 & 버전 정책
- 파일명은 **날짜 기준**(`YYYY-MM-DD`)으로 생성됩니다.
- **같은 날짜로 재실행 시 기존 파일을 덮어씁니다.** (최신 결과 유지)
- 이전 결과를 보존하려면 실행 전 파일명을 백업하거나, 향후 캐시 옵션(아래 로드맵 참고)을 사용하세요.

### 📝 오류 리포트
실행 중 발생한 문제(맛집 0건, 파싱 실패 등)는 `errors` 배열에 수집되어
**Markdown 리포트 최하단**과 **JSON 파일**에 함께 기록됩니다.
문제가 없으면 "오류 없음"으로 표시됩니다.

---

## 🧩 설계 노트 (기술 선택 이유)

### 1. 왜 LLM 응답을 JSON으로 강제했나?
- ✅ **구조화**: `recommended_city` 등 필드를 코드에서 바로 추출 가능
- ✅ **후처리 용이**: 파이썬 dict로 변환 후 검증·저장·재사용이 간편
- ✅ **안정성**: 필수 키/타입 검증으로 잘못된 응답 조기 차단
- ⚠️ 단점: 자연어 응답보다 프롬프트 제약이 강해 실패 시 재시도 필요

### 2. HTTP 메서드 선택 근거 (GET vs POST)
| API | 메서드 | 이유 |
|-----|--------|------|
| Kakao Local 검색 | **GET** | 데이터를 **조회**만 하므로 (서버 상태 변경 없음) |
| OpenAI Chat | **POST** | 프롬프트를 **본문(body)** 으로 전송해 결과를 **생성**하므로 |

### 3. 검증 실패 시 에러 메시지 포맷
- 필수 키 누락: `"필수 키 누락: {key}"`
- 타입 불일치: `"타입 오류: {key}"`
- 맛집 0건: `"맛집 검색 결과 0건"`
> LLM 스키마(`recommended_city`, `weather`, `events`, `reason`) 변경 시
> 이 포맷과 `required_keys` 딕셔너리를 함께 수정하세요.

---

## 🔧 문제 해결 (Troubleshooting)

### API 키 401 / 403 오류 체크리스트
| 확인 항목 | 점검 내용 |
|-----------|-----------|
| 🔑 키 값 | `.env`의 키에 오타·공백·따옴표가 없는지 |
| 🛡️ 권한 | Kakao 앱에 **REST API 키 / 플랫폼(Web) 등록**이 됐는지 |
| 📊 쿼터 | API 호출 한도(무료 쿼터)를 초과하지 않았는지 |
| 📨 헤더 | `Authorization: KakaoAK {키}` 형식이 올바른지 |
| 🌐 네트워크 | 방화벽·프록시가 요청을 차단하지 않는지 |

---

## ⚠️ 주의사항 (보안 필수!)

- 🔒 `.env` 파일에는 **API 키가 들어있으므로 절대 GitHub에 올리지 마세요.**
- 🔒 `.gitignore`에 반드시 `.env`를 추가하세요.
- 🔒 API 키가 유출되면 **즉시 재발급**받으세요.
- 🔒 코드, README, 결과 파일 어디에도 실제 키 값을 작성하지 마세요.

### 🖥️ 운영환경(서버/CI) 환경변수 주입 예시
```bash
# Linux/CI (예: GitHub Actions, 서버 배포 시)
export OPENAI_API_KEY="sk-..."
export KAKAO_REST_API_KEY="..."
```
> CI에서는 **Secrets 기능**(예: GitHub Actions Secrets)에 키를 등록해 주입하세요.

---

## 🧰 사용 기술

- **Python 3.10+**
- **OpenAI API** — 여행지 추천 & 리포트 일정 생성 (POST)
- **Kakao Local API** — 맛집(장소) 검색 (GET)
- **python-dotenv** — 환경변수(.env) 관리

---

## 🗺️ 향후 개선 로드맵

- [완] **지도 API 추상화**: `search_place()`를 인터페이스로 분리해 다른 공급자(네이버 등) 교체 가능하게
- [완] **오류 누적 저장**: 과거 `results` JSON을 읽어 `errors`를 병합
- [완] **캐시/재사용**: 같은 날짜 결과가 있으면 API 호출을 건너뛰는 옵션
- [완] **도시명 정규화**: 오탈자·동의어 보정, 세부 지역 추출 전처리
- [비] **맛집 0건 대응**: 대체 키워드·근접 지역 자동 확장
- [완] **재시도 프롬프트 보정**: 파싱 실패 시 정규표현식 추출 + 프롬프트 강화
## 🧩 설계 노트 (확장) — 향후 전략 상세

---

### 4. 지도 API 공급자 교체 전략 
현재 `search_place()`는 Kakao Local API에 고정되어 있습니다.
공급자 교체를 위해 아래처럼 **래퍼 인터페이스**로 분리하는 설계를 권장합니다.

```python
# 인터페이스(추상) — 모든 공급자가 이 형태를 따름
class PlaceSearcher:
    def search(self, keyword: str) -> list[dict]:
        raise NotImplementedError

# Kakao 구현체
class KakaoSearcher(PlaceSearcher):
    def search(self, keyword):
        # 기존 Kakao 호출 로직
        ...

# Naver 등 다른 공급자로 교체 시 새 클래스만 추가
```
> **교체 지침**: 새 공급자는 `PlaceSearcher`를 상속해 `search()`만 구현하면 되며,
> 반환 형식(`[{name, address}, ...]`)만 맞추면 상위 코드는 수정 불필요합니다.

---

### 5. 오류 누적 저장 전략
현재는 실행할 때마다 `errors`가 새로 시작됩니다.
과거 로그를 병합하려면 아래 로직을 도입합니다.

```python
import os, json

def load_previous_errors(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("errors", [])
    return []

# 사용: 기존 오류 + 이번 실행 오류 병합
merged_errors = load_previous_errors(json_path) + errors
```
> `--merge-errors` 옵션을 argparse에 추가해 선택적으로 병합하도록 설계합니다.

---

### 6. 재시도 시 프롬프트 보정 & 파싱 보완 전략
파싱 실패 시 단순 재시도를 넘어 아래 전략을 적용합니다.

**(1) 프롬프트 보정** — 재시도 시 제약을 더 강하게:
```
"이전 응답이 JSON 파싱에 실패했습니다.
 코드블록(```)이나 설명 없이 순수 JSON 객체만 출력하세요."
```

**(2) 파싱 보완** — 정규표현식으로 JSON 부분만 추출:
```python
import re, json

def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)  # 첫 {부터 마지막 }까지
    if match:
        return json.loads(match.group())
    raise ValueError("JSON 추출 실패")
```
> 이렇게 하면 LLM이 앞뒤에 설명을 붙여도 JSON만 안전하게 뽑아낼 수 있습니다.

---

### 7. 결과 캐시 / 재사용 전략
같은 날짜로 재실행 시 API 재호출을 막아 비용·시간을 절약합니다.

```python
def get_cached_or_run(date, force=False):
    path = f"results/travel_data_{date}.json"
    if os.path.exists(path) and not force:
        print("♻️ 캐시된 결과를 재사용합니다.")
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return run_full_pipeline(date)  # 없으면 실제 실행
```
> `--force` 옵션으로 캐시를 무시하고 새로 실행할 수 있게 설계합니다.

---

### 8. 추천 도시명 정규화 전략
LLM이 반환한 도시명이 부정확할 때를 대비한 전처리 단계입니다.

```python
CITY_ALIAS = {"서울시": "서울", "제주도": "제주", "부산광역시": "부산"}

def normalize_city(city: str) -> str:
    city = city.strip()
    city = CITY_ALIAS.get(city, city)        # 동의어 보정
    city = re.sub(r"(특별시|광역시|도)$", "", city)  # 접미사 제거
    return city

# 사용
keyword = f"{normalize_city(city)} 맛집"
```
> **처리 순서**: 공백 제거 → 동의어 매핑 → 접미사 제거 → (실패 시 LLM 재질문).
> 오탈자가 심하면 맛집 검색 0건을 유발하므로 검색 전 반드시 정규화합니다.
