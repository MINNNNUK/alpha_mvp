#!/usr/bin/env python3
"""
상세 매칭 확인 스크립트
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

def detailed_matching_check(supabase: Client):
    """상세 매칭 확인"""
    print("🔍 상세 매칭 확인")
    print("=" * 50)
    
    # alpha_companies에서 첫 번째 회사 정보 확인
    company_result = supabase.table('alpha_companies').select('"No.", "사업아이템 한 줄 소개"').eq('"No."', 1).execute()
    
    if company_result.data:
        company = company_result.data[0]
        company_no = company.get('No.')
        business_item = company.get('사업아이템 한 줄 소개', '')
        
        print(f"📋 회사 정보 (No.{company_no}):")
        print(f"   사업아이템: '{business_item}'")
        print(f"   길이: {len(business_item)}자")
        
        # recommendations2에서 해당 회사의 사업아이템과 정확히 일치하는지 확인
        print(f"\n🔍 recommendations2 테이블에서 검색:")
        try:
            # 정확한 일치 검색
            exact_result = supabase.table('recommendations2').select('*').eq('기업명', business_item).execute()
            print(f"   정확한 일치: {len(exact_result.data)}개")
            
            # 부분 일치 검색 (ILIKE 사용)
            partial_result = supabase.table('recommendations2').select('*').ilike('기업명', f'%{business_item}%').execute()
            print(f"   부분 일치 (ILIKE): {len(partial_result.data)}개")
            
            # 포함 검색 (일부 텍스트만)
            if len(business_item) > 10:
                short_text = business_item[:20]  # 처음 20자만
                short_result = supabase.table('recommendations2').select('*').ilike('기업명', f'%{short_text}%').execute()
                print(f"   부분 텍스트 ({short_text}): {len(short_result.data)}개")
            
            # recommendations2의 모든 기업명 샘플 확인
            all_rec2 = supabase.table('recommendations2').select('기업명').limit(10).execute()
            print(f"\n   recommendations2 기업명 샘플:")
            for i, record in enumerate(all_rec2.data):
                company_name = record.get('기업명', 'N/A')
                print(f"     {i+1}. '{company_name}' (길이: {len(str(company_name))})")
                
                # 우리 사업아이템과 비교
                if str(company_name).strip() == business_item.strip():
                    print(f"        ✅ 정확한 일치!")
                elif business_item in str(company_name):
                    print(f"        ✅ 부분 포함!")
                elif str(company_name) in business_item:
                    print(f"        ✅ 역방향 포함!")
                    
        except Exception as e:
            print(f"   ❌ 오류: {e}")
        
        # recommendations3_active에서도 동일하게 확인
        print(f"\n🔍 recommendations3_active 테이블에서 검색:")
        try:
            # 정확한 일치 검색
            exact_result = supabase.table('recommendations3_active').select('*').eq('기업명', business_item).execute()
            print(f"   정확한 일치: {len(exact_result.data)}개")
            
            # 부분 일치 검색
            partial_result = supabase.table('recommendations3_active').select('*').ilike('기업명', f'%{business_item}%').execute()
            print(f"   부분 일치 (ILIKE): {len(partial_result.data)}개")
            
            # recommendations3_active의 모든 기업명 샘플 확인
            all_rec3 = supabase.table('recommendations3_active').select('기업명').limit(10).execute()
            print(f"\n   recommendations3_active 기업명 샘플:")
            for i, record in enumerate(all_rec3.data):
                company_name = record.get('기업명', 'N/A')
                print(f"     {i+1}. '{company_name}' (길이: {len(str(company_name))})")
                
                # 우리 사업아이템과 비교
                if str(company_name).strip() == business_item.strip():
                    print(f"        ✅ 정확한 일치!")
                elif business_item in str(company_name):
                    print(f"        ✅ 부분 포함!")
                elif str(company_name) in business_item:
                    print(f"        ✅ 역방향 포함!")
                    
        except Exception as e:
            print(f"   ❌ 오류: {e}")

def main():
    """메인 함수"""
    print("🔍 상세 매칭 확인")
    print("=" * 40)
    
    supabase = init_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return
    
    detailed_matching_check(supabase)

if __name__ == "__main__":
    main()







