"""
Supabase 설정 및 초기화 스크립트
"""
import os
import sys
from pathlib import Path

def create_env_file():
    """환경변수 파일 생성"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env 파일이 이미 존재합니다.")
        return True
    
    print("📝 .env 파일을 생성합니다...")
    
    # 사용자 입력 받기
    print("\nSupabase 프로젝트 정보를 입력해주세요:")
    print("(Supabase 대시보드 > Settings > API에서 확인할 수 있습니다)")
    
    url = input("SUPABASE_URL: ").strip()
    key = input("SUPABASE_KEY: ").strip()
    
    if not url or not key:
        print("❌ URL과 Key를 모두 입력해주세요.")
        return False
    
    # .env 파일 생성
    env_content = f"""# Supabase 설정
SUPABASE_URL={url}
SUPABASE_KEY={key}
"""
    
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print("✅ .env 파일이 생성되었습니다.")
        return True
    except Exception as e:
        print(f"❌ .env 파일 생성 실패: {e}")
        return False

def check_dependencies():
    """의존성 확인"""
    print("📦 Python 패키지 의존성 확인...")
    
    required_packages = [
        'streamlit',
        'pandas', 
        'supabase',
        'dotenv',
        'altair',
        'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (설치 필요)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n설치가 필요한 패키지: {', '.join(missing_packages)}")
        print("다음 명령어로 설치하세요:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ 모든 의존성이 설치되어 있습니다.")
    return True

def main():
    """메인 설정 함수"""
    print("=" * 60)
    print("🏛️ 정부지원사업 맞춤 추천 시스템 - Supabase 설정")
    print("=" * 60)
    
    # 1. 의존성 확인
    if not check_dependencies():
        print("\n❌ 의존성 설치 후 다시 실행해주세요.")
        return
    
    # 2. 환경변수 파일 생성
    if not create_env_file():
        print("\n❌ 환경변수 설정에 실패했습니다.")
        return
    
    # 3. 연결 테스트
    print("\n🔗 Supabase 연결 테스트...")
    try:
        from test_supabase_connection import test_connection
        if test_connection():
            print("\n🎉 설정이 완료되었습니다!")
            print("\n다음 단계:")
            print("1. python migrate_to_supabase.py  # 데이터 마이그레이션")
            print("2. streamlit run app_supabase.py  # 앱 실행")
        else:
            print("\n❌ 연결 테스트에 실패했습니다. 설정을 확인해주세요.")
    except Exception as e:
        print(f"\n❌ 연결 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
