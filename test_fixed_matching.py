#!/usr/bin/env python3
"""
수정된 매칭 로직 테스트
"""
import os
import pandas as pd
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

def test_fixed_matching():
    """수정된 매칭 로직 테스트"""
    print("🔍 수정된 매칭 로직 테스트")
    print("=" * 50)
    
    supabase = init_supabase()
    if not supabase:
        return
    
    try:
        # 첫 번째 회사 데이터 가져오기
        company_result = supabase.table('alpha_companies2').select('*').limit(1).execute()
        if not company_result.data:
            print("   ❌ 회사 데이터가 없습니다.")
            return
        
        company = company_result.data[0]
        company_id = company['No.']
        company_name = company['기업명']
        
        print(f"   📋 테스트 회사:")
        print(f"      ID: {company_id}")
        print(f"      기업명: {company_name}")
        
        # 수정된 매칭 로직 테스트
        print(f"\n   🔍 수정된 매칭 시도:")
        print(f"      검색어: '%{company_name}%'")
        
        # ILIKE 검색
        recommend_result = supabase.table('recommend2').select('*').ilike('기업명', f'%{company_name}%').execute()
        
        print(f"      ILIKE 결과: {len(recommend_result.data)}개")
        
        if recommend_result.data:
            print(f"      ✅ 매칭된 추천:")
            for idx, rec in enumerate(recommend_result.data[:5]):
                print(f"         {idx+1}. {rec.get('기업명', 'N/A')} - {rec.get('공고제목', 'N/A')} (점수: {rec.get('총점수', 'N/A')})")
        else:
            print(f"      ❌ 매칭된 추천이 없습니다.")
        
        # 모든 회사에 대해 테스트
        print(f"\n   🔍 모든 회사 매칭 테스트:")
        all_companies = supabase.table('alpha_companies2').select('"No.", "기업명"').execute()
        
        matched_count = 0
        for company in all_companies.data:
            company_id = company['No.']
            company_name = company['기업명']
            
            recommend_result = supabase.table('recommend2').select('*').ilike('기업명', f'%{company_name}%').execute()
            
            if recommend_result.data:
                matched_count += 1
                print(f"      ✅ {company_name}: {len(recommend_result.data)}개 추천")
            else:
                print(f"      ❌ {company_name}: 0개 추천")
        
        print(f"\n   📊 매칭 결과 요약:")
        print(f"      총 회사 수: {len(all_companies.data)}")
        print(f"      매칭된 회사 수: {matched_count}")
        print(f"      매칭률: {matched_count/len(all_companies.data)*100:.1f}%")
        
    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")

def main():
    """메인 함수"""
    print("🧪 수정된 매칭 로직 테스트 시작")
    print("=" * 60)
    
    test_fixed_matching()
    
    print("\n" + "=" * 60)
    print("✅ 테스트 완료")

if __name__ == "__main__":
    main()

