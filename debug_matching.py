#!/usr/bin/env python3
"""
데이터 매칭 디버깅 스크립트
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

def debug_company_data():
    """회사 데이터 디버깅"""
    print("🔍 회사 데이터 디버깅")
    print("=" * 50)
    
    supabase = init_supabase()
    if not supabase:
        return
    
    # alpha_companies2 데이터 확인
    try:
        result = supabase.table('alpha_companies2').select('*').limit(5).execute()
        df = pd.DataFrame(result.data)
        
        print(f"📊 alpha_companies2 테이블 (상위 5개):")
        print(f"   총 레코드 수: {len(result.data)}")
        if not df.empty:
            print(f"   컬럼: {list(df.columns)}")
            print("\n   샘플 데이터:")
            for idx, row in df.iterrows():
                print(f"   {idx+1}. No.: {row.get('No.', 'N/A')}")
                print(f"      사업아이템: {row.get('사업아이템 한 줄 소개', 'N/A')}")
                print(f"      기업명: {row.get('기업명', 'N/A')}")
                print()
        else:
            print("   ❌ 데이터가 없습니다.")
    except Exception as e:
        print(f"   ❌ alpha_companies2 조회 실패: {e}")

def debug_recommend_data():
    """추천 데이터 디버깅"""
    print("\n🔍 추천 데이터 디버깅")
    print("=" * 50)
    
    supabase = init_supabase()
    if not supabase:
        return
    
    # recommend2 데이터 확인
    try:
        result = supabase.table('recommend2').select('*').limit(5).execute()
        df = pd.DataFrame(result.data)
        
        print(f"📊 recommend2 테이블 (상위 5개):")
        print(f"   총 레코드 수: {len(result.data)}")
        if not df.empty:
            print(f"   컬럼: {list(df.columns)}")
            print("\n   샘플 데이터:")
            for idx, row in df.iterrows():
                print(f"   {idx+1}. 기업명: {row.get('기업명', 'N/A')}")
                print(f"      공고제목: {row.get('공고제목', 'N/A')}")
                print(f"      총점수: {row.get('총점수', 'N/A')}")
                print()
        else:
            print("   ❌ 데이터가 없습니다.")
    except Exception as e:
        print(f"   ❌ recommend2 조회 실패: {e}")

def debug_matching():
    """매칭 로직 디버깅"""
    print("\n🔍 매칭 로직 디버깅")
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
        business_item = company['사업아이템 한 줄 소개']
        
        print(f"   📋 테스트 회사:")
        print(f"      ID: {company_id}")
        print(f"      사업아이템: {business_item}")
        
        # 기업명 추출 로직 테스트
        if ' - ' in business_item:
            business_item_only = business_item.split(' - ', 1)[1]
        else:
            business_item_only = business_item
        
        print(f"      추출된 키워드: {business_item_only}")
        
        # 매칭 시도
        print(f"\n   🔍 매칭 시도:")
        print(f"      검색어: '%{business_item_only}%'")
        
        # ILIKE 검색
        recommend_result = supabase.table('recommend2').select('*').ilike('기업명', f'%{business_item_only}%').execute()
        
        print(f"      ILIKE 결과: {len(recommend_result.data)}개")
        
        if recommend_result.data:
            print(f"      매칭된 추천:")
            for idx, rec in enumerate(recommend_result.data[:3]):
                print(f"         {idx+1}. {rec.get('기업명', 'N/A')} - {rec.get('공고제목', 'N/A')}")
        else:
            print(f"      ❌ 매칭된 추천이 없습니다.")
            
            # 전체 기업명 목록 확인
            all_recommend_result = supabase.table('recommend2').select('기업명').limit(10).execute()
            print(f"\n      📋 recommend2의 기업명 샘플:")
            for idx, rec in enumerate(all_recommend_result.data):
                print(f"         {idx+1}. {rec.get('기업명', 'N/A')}")
        
    except Exception as e:
        print(f"   ❌ 매칭 디버깅 실패: {e}")

def main():
    """메인 함수"""
    print("🐛 데이터 매칭 디버깅 시작")
    print("=" * 60)
    
    debug_company_data()
    debug_recommend_data()
    debug_matching()
    
    print("\n" + "=" * 60)
    print("✅ 디버깅 완료")

if __name__ == "__main__":
    main()

