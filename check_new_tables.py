#!/usr/bin/env python3
"""
새로운 테이블들의 존재 여부 확인 스크립트
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

def check_table_exists(supabase: Client, table_name: str):
    """특정 테이블의 존재 여부와 구조 확인"""
    try:
        # 테이블 존재 확인 (첫 번째 레코드만 가져와서 테스트)
        result = supabase.table(table_name).select('*').limit(1).execute()
        
        if result.data is not None:
            print(f"✅ {table_name} 테이블 존재")
            
            # 테이블 구조 확인
            if result.data:
                print(f"   📊 컬럼 수: {len(result.data[0])}개")
                print(f"   📋 컬럼명: {list(result.data[0].keys())}")
                
                # 전체 레코드 수 확인
                count_result = supabase.table(table_name).select('*', count='exact').execute()
                total_count = count_result.count if hasattr(count_result, 'count') else len(result.data)
                print(f"   📈 총 레코드 수: {total_count}개")
            else:
                print(f"   ⚠️ 테이블은 존재하지만 데이터가 없습니다.")
            
            return True
        else:
            print(f"❌ {table_name} 테이블이 존재하지 않습니다.")
            return False
            
    except Exception as e:
        print(f"❌ {table_name} 테이블 확인 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🔍 새로운 테이블들 존재 여부 확인")
    print("=" * 50)
    
    supabase = init_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return
    
    # 확인할 테이블 목록
    tables_to_check = [
        'alpha_companies2',
        'biz2', 
        'kstartup2',
        'recommend2',
        'recommend_active2'
    ]
    
    existing_tables = []
    missing_tables = []
    
    for table_name in tables_to_check:
        print(f"\n🔍 {table_name} 테이블 확인 중...")
        if check_table_exists(supabase, table_name):
            existing_tables.append(table_name)
        else:
            missing_tables.append(table_name)
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 확인 결과 요약")
    print("=" * 50)
    
    if existing_tables:
        print(f"✅ 존재하는 테이블 ({len(existing_tables)}개):")
        for table in existing_tables:
            print(f"   - {table}")
    
    if missing_tables:
        print(f"\n❌ 존재하지 않는 테이블 ({len(missing_tables)}개):")
        for table in missing_tables:
            print(f"   - {table}")
    
    print(f"\n총 {len(tables_to_check)}개 테이블 중 {len(existing_tables)}개 존재")

if __name__ == "__main__":
    main()

