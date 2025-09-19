#!/usr/bin/env python3
"""
추천 데이터 문제 디버깅 스크립트
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

def check_all_tables(supabase: Client):
    """모든 관련 테이블 확인"""
    tables_to_check = [
        'alpha_companies',
        'announcements', 
        'recommendations',
        'recommendations2',
        'recommendations3_active',
        'notification_states'
    ]
    
    print("🔍 모든 테이블 데이터 확인")
    print("=" * 50)
    
    for table_name in tables_to_check:
        try:
            result = supabase.table(table_name).select('*').limit(5).execute()
            count_result = supabase.table(table_name).select('*', count='exact').execute()
            
            print(f"\n📊 {table_name} 테이블:")
            print(f"   총 레코드 수: {count_result.count}")
            
            if result.data:
                print(f"   컬럼: {list(result.data[0].keys())}")
                if table_name == 'alpha_companies':
                    for i, record in enumerate(result.data[:3]):
                        print(f"   {i+1}. No.{record.get('No.', 'N/A')} - {record.get('사업아이템 한 줄 소개', 'N/A')[:50]}...")
            else:
                print("   데이터 없음")
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")

def check_recommendation_matching(supabase: Client):
    """추천 데이터와 회사 매칭 확인"""
    print("\n🔗 추천 데이터와 회사 매칭 확인")
    print("=" * 50)
    
    try:
        # alpha_companies에서 첫 번째 회사 확인
        companies_result = supabase.table('alpha_companies').select('"No.", "사업아이템 한 줄 소개"').limit(3).execute()
        
        if companies_result.data:
            print("📋 회사 정보:")
            for company in companies_result.data:
                company_no = company.get('No.')
                company_name = company.get('사업아이템 한 줄 소개', '')[:30]
                print(f"   No.{company_no}: {company_name}...")
                
                # 해당 회사의 추천 데이터 확인
                print(f"\n   🔍 No.{company_no} 회사의 추천 데이터:")
                
                # recommendations 테이블 확인
                try:
                    rec_result = supabase.table('recommendations').select('*').eq('company_id', company_no).execute()
                    print(f"      recommendations: {len(rec_result.data)}개")
                except Exception as e:
                    print(f"      recommendations: 오류 - {e}")
                
                # recommendations2 테이블 확인
                try:
                    rec2_result = supabase.table('recommendations2').select('*').limit(3).execute()
                    print(f"      recommendations2: {len(rec2_result.data)}개 (전체)")
                    if rec2_result.data:
                        # 기업명으로 매칭 시도
                        company_name_short = company_name.split(' - ')[0] if ' - ' in company_name else company_name
                        matching_recs = [r for r in rec2_result.data if company_name_short in str(r.get('기업명', ''))]
                        print(f"      기업명 매칭: {len(matching_recs)}개")
                except Exception as e:
                    print(f"      recommendations2: 오류 - {e}")
                
                # recommendations3_active 테이블 확인
                try:
                    rec3_result = supabase.table('recommendations3_active').select('*').limit(3).execute()
                    print(f"      recommendations3_active: {len(rec3_result.data)}개 (전체)")
                    if rec3_result.data:
                        # 기업명으로 매칭 시도
                        company_name_short = company_name.split(' - ')[0] if ' - ' in company_name else company_name
                        matching_recs = [r for r in rec3_result.data if company_name_short in str(r.get('기업명', ''))]
                        print(f"      기업명 매칭: {len(matching_recs)}개")
                except Exception as e:
                    print(f"      recommendations3_active: 오류 - {e}")
                
                print()
        else:
            print("❌ 회사 데이터가 없습니다.")
            
    except Exception as e:
        print(f"❌ 매칭 확인 실패: {e}")

def main():
    """메인 함수"""
    print("🐛 추천 데이터 문제 디버깅")
    print("=" * 40)
    
    supabase = init_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return
    
    check_all_tables(supabase)
    check_recommendation_matching(supabase)

if __name__ == "__main__":
    main()







