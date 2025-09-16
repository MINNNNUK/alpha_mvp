"""
Supabase 설정 파일
"""
import os
from dotenv import load_dotenv

# .env 파일 로드 (로컬 개발용)
load_dotenv()

# Streamlit Cloud에서는 secrets를 사용, 로컬에서는 환경변수 사용
def get_supabase_config():
    try:
        import streamlit as st
        # Streamlit Cloud의 secrets 사용
        return st.secrets["supabase"]["url"], st.secrets["supabase"]["key"]
    except:
        # 로컬 개발 환경에서는 환경변수 사용
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        return url, key

# Supabase 설정 가져오기
SUPABASE_URL, SUPABASE_KEY = get_supabase_config()

# 설정이 없는 경우 에러
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Supabase 설정이 없습니다.\n"
        "로컬 개발: .env 파일에 SUPABASE_URL과 SUPABASE_KEY를 설정하세요.\n"
        "Streamlit Cloud: Secrets에 supabase.url과 supabase.key를 설정하세요."
    )
