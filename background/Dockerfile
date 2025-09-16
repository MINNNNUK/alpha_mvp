FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치를 위한 requirements.txt 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 앱 파일들 복사
COPY . .

# 포트 노출
EXPOSE 8501

# Streamlit 앱 실행
CMD ["streamlit", "run", "app_supabase.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
