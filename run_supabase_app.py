#!/usr/bin/env python3
"""
Supabase 연동 앱 실행 스크립트
"""
import os
import sys
import subprocess
from pathlib import Path

def check_env_file():
    """환경변수 파일 확인"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env 파일이 없습니다.")
        print("다음 중 하나를 실행하세요:")
        print("1. python setup_supabase.py  # 자동 설정")
        print("2. cp env_example.txt .env   # 수동 설정")
        return False
    return True

def check_dependencies():
    """의존성 확인"""
    try:
        import streamlit
        import pandas
        import supabase
        from dotenv import load_dotenv
        return True
    except ImportError as e:
        print(f"❌ 필요한 패키지가 설치되지 않았습니다: {e}")
        print("다음 명령어로 설치하세요: pip install -r requirements.txt")
        return False

def test_connection():
    """Supabase 연결 테스트"""
    try:
        from test_supabase_connection import test_connection
        return test_connection()
    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🚀 Supabase 연동 앱 실행 중...")
    
    # 1. 환경변수 파일 확인
    if not check_env_file():
        return
    
    # 2. 의존성 확인
    if not check_dependencies():
        return
    
    # 3. 연결 테스트 (선택사항)
    test_conn = input("Supabase 연결을 테스트하시겠습니까? (y/N): ").strip().lower()
    if test_conn == 'y':
        if not test_connection():
            print("❌ 연결 테스트에 실패했습니다. 설정을 확인해주세요.")
            return
    
    # 4. 앱 실행
    print("🎉 앱을 실행합니다...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app_supabase.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 앱이 종료되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 앱 실행 실패: {e}")

if __name__ == "__main__":
    main()
