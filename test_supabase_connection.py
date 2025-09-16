"""
Supabase 연결 테스트 스크립트
"""
import os
import sys
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

def test_connection():
    """Supabase 연결 테스트"""
    print("🔗 Supabase 연결 테스트 시작...")
    print(f"URL: {SUPABASE_URL}")
    print(f"Key: {SUPABASE_KEY[:20]}...")
    
    try:
        # Supabase 클라이언트 생성
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase 클라이언트 생성 성공")
        
        # 테이블 존재 확인
        tables = ['companies', 'announcements', 'recommendations', 'notification_states']
        
        for table in tables:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                print(f"✅ {table} 테이블 접근 성공 (레코드 수: {len(result.data)})")
            except Exception as e:
                print(f"❌ {table} 테이블 접근 실패: {e}")
                return False
        
        print("\n🎉 모든 테스트 통과! Supabase 연결이 정상적으로 작동합니다.")
        return True
        
    except Exception as e:
        print(f"❌ Supabase 연결 실패: {e}")
        print("\n해결 방법:")
        print("1. .env 파일이 존재하는지 확인")
        print("2. SUPABASE_URL과 SUPABASE_KEY가 올바른지 확인")
        print("3. Supabase 프로젝트가 활성화되어 있는지 확인")
        return False

def test_data_operations():
    """데이터 CRUD 작업 테스트"""
    print("\n📊 데이터 작업 테스트 시작...")
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 테스트 회사 데이터
        test_company = {
            'name': '테스트 회사',
            'business_type': '법인',
            'region': '서울',
            'years': 3,
            'stage': '초기',
            'industry': 'IT',
            'keywords': ['테스트', '개발'],
            'preferred_uses': ['R&D'],
            'preferred_budget': '중간'
        }
        
        # INSERT 테스트
        result = supabase.table('companies').insert(test_company).execute()
        company_id = result.data[0]['id']
        print(f"✅ 회사 데이터 삽입 성공 (ID: {company_id})")
        
        # SELECT 테스트
        result = supabase.table('companies').select('*').eq('id', company_id).execute()
        if result.data:
            print("✅ 회사 데이터 조회 성공")
        
        # UPDATE 테스트
        result = supabase.table('companies').update({'name': '테스트 회사 (수정)'}).eq('id', company_id).execute()
        print("✅ 회사 데이터 수정 성공")
        
        # DELETE 테스트
        result = supabase.table('companies').delete().eq('id', company_id).execute()
        print("✅ 회사 데이터 삭제 성공")
        
        print("🎉 모든 데이터 작업 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"❌ 데이터 작업 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Supabase 연결 및 데이터 작업 테스트")
    print("=" * 50)
    
    # 연결 테스트
    if test_connection():
        # 데이터 작업 테스트
        test_data_operations()
    
    print("\n" + "=" * 50)
