#!/usr/bin/env python3
"""
alpha_companies 테이블 구조 확인 스크립트
"""

import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

def init_supabase():
    """Supabase 클라이언트 초기화"""
    try:
        url = os.getenv("SUPABASE_URL", SUPABASE_URL)
        key = os.getenv("SUPABASE_KEY", SUPABASE_KEY)
        
        if url == "https://demo.supabase.co" or key == "demo-key":
            print("⚠️ 데모 모드 - 실제 Supabase 설정이 필요합니다.")
            return None
        
        return create_client(url, key)
    except Exception as e:
        print(f"Supabase 연결 실패: {e}")
        return None

def check_table_structure(supabase: Client):
    """테이블 구조 확인"""
    try:
        # 첫 번째 레코드만 가져와서 컬럼 구조 확인
        result = supabase.table('alpha_companies').select('*').limit(1).execute()
        
        if result.data:
            print("📊 alpha_companies 테이블 컬럼 구조:")
            print("=" * 50)
            
            first_record = result.data[0]
            for i, (key, value) in enumerate(first_record.items(), 1):
                print(f"{i:2}. {key}: {type(value).__name__}")
            
            print(f"\n총 {len(first_record)}개 컬럼")
            
            # 모든 데이터 조회해서 No. 범위 확인
            all_result = supabase.table('alpha_companies').select('"No."').execute()
            if all_result.data:
                numbers = [record['No.'] for record in all_result.data if record.get('No.')]
                print(f"\nNo. 범위: {min(numbers)} ~ {max(numbers)} (총 {len(numbers)}개)")
                
        else:
            print("❌ 테이블에 데이터가 없습니다.")
            
    except Exception as e:
        print(f"❌ 테이블 구조 확인 실패: {e}")

def main():
    """메인 함수"""
    print("🔍 alpha_companies 테이블 구조 확인")
    print("=" * 40)
    
    supabase = init_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return
    
    check_table_structure(supabase)

if __name__ == "__main__":
    main()






