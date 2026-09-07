import os
from dotenv import load_dotenv

# .env 파일에서 환경변수 불러오기
load_dotenv()

# OpenAI API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Kakao API 키 (이름 맞춤!)
KAKAO_API_KEY = os.getenv("KAKAO_REST_API_KEY")  # ← 여기 수정!

# 키가 제대로 불러와졌는지 확인
if not OPENAI_API_KEY:
    print("⚠️ OpenAI API 키를 찾을 수 없어요!")
if not KAKAO_API_KEY:
    print("⚠️ Kakao API 키를 찾을 수 없어요!")