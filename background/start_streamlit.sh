#!/bin/bash

# Streamlit 앱 시작 스크립트
echo "Starting Streamlit app..."

# 현재 디렉토리로 이동
cd /Users/minkim/git_test/kpmg-2025/data2/supabase1

# 환경 변수 로드 (있다면)
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Streamlit 앱 실행
streamlit run app_supabase.py --server.port 8501 --server.address 0.0.0.0
