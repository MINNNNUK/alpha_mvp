#!/usr/bin/env python3
"""
announcements 데이터 구조 디버깅
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

def debug_announcements():
    """announcements 데이터 구조 디버깅"""
    print("🔍 announcements 데이터 구조 디버깅")
    print("=" * 50)
    
    supabase = init_supabase()
    if not supabase:
        return
    
    # biz2 테이블 확인
    try:
        print("📊 biz2 테이블:")
        biz_result = supabase.table('biz2').select('*').limit(3).execute()
        biz_df = pd.DataFrame(biz_result.data)
        print(f"   레코드 수: {len(biz_df)}")
        if not biz_df.empty:
            print(f"   컬럼: {list(biz_df.columns)}")
            print(f"   샘플 데이터:")
            for idx, row in biz_df.iterrows():
                print(f"      {idx+1}. {row.get('공고명', 'N/A')}")
    except Exception as e:
        print(f"   ❌ biz2 조회 실패: {e}")
    
    # kstartup2 테이블 확인
    try:
        print("\n📊 kstartup2 테이블:")
        kstartup_result = supabase.table('kstartup2').select('*').limit(3).execute()
        kstartup_df = pd.DataFrame(kstartup_result.data)
        print(f"   레코드 수: {len(kstartup_df)}")
        if not kstartup_df.empty:
            print(f"   컬럼: {list(kstartup_df.columns)}")
            print(f"   샘플 데이터:")
            for idx, row in kstartup_df.iterrows():
                print(f"      {idx+1}. {row.get('사업공고명', 'N/A')}")
    except Exception as e:
        print(f"   ❌ kstartup2 조회 실패: {e}")

def test_announcements_merge():
    """announcements 통합 테스트"""
    print("\n🔍 announcements 통합 테스트")
    print("=" * 50)
    
    supabase = init_supabase()
    if not supabase:
        return
    
    try:
        # biz2 데이터 로드
        biz_result = supabase.table('biz2').select('*').execute()
        biz_df = pd.DataFrame(biz_result.data)
        
        # kstartup2 데이터 로드
        kstartup_result = supabase.table('kstartup2').select('*').execute()
        kstartup_df = pd.DataFrame(kstartup_result.data)
        
        print(f"biz2 레코드 수: {len(biz_df)}")
        print(f"kstartup2 레코드 수: {len(kstartup_df)}")
        
        # biz2 데이터 정규화
        if not biz_df.empty:
            biz_df['source'] = 'Bizinfo'
            biz_df['id'] = biz_df['번호'].astype(str)
            biz_df['title'] = biz_df['공고명']
            biz_df['agency'] = biz_df['사업수행기관']
            biz_df['region'] = ''
            biz_df['due_date'] = biz_df['신청종료일자']
            biz_df['info_session_date'] = biz_df['신청시작일자']
            biz_df['url'] = biz_df['공고상세URL']
            biz_df['amount_text'] = ''
            biz_df['amount_krw'] = None
            biz_df['stage'] = ''
            biz_df['update_type'] = '신규'
            biz_df['budget_band'] = '중간'
            biz_df['allowed_uses'] = []
            biz_df['keywords'] = []
        
        # kstartup2 데이터 정규화
        if not kstartup_df.empty:
            kstartup_df['source'] = 'K-Startup'
            kstartup_df['id'] = kstartup_df['공고일련번호'].astype(str)
            kstartup_df['title'] = kstartup_df['사업공고명']
            kstartup_df['agency'] = kstartup_df['주관기관']
            kstartup_df['region'] = kstartup_df['지원지역']
            kstartup_df['due_date'] = kstartup_df['공고접수종료일시']
            kstartup_df['info_session_date'] = kstartup_df['공고접수시작일시']
            kstartup_df['url'] = kstartup_df['상세페이지 url']
            kstartup_df['amount_text'] = ''
            kstartup_df['amount_krw'] = None
            kstartup_df['stage'] = kstartup_df['사업업력']
            kstartup_df['update_type'] = '신규'
            kstartup_df['budget_band'] = '중간'
            kstartup_df['allowed_uses'] = []
            kstartup_df['keywords'] = []
        
        # 공통 컬럼 정의
        common_columns = ['id', 'title', 'agency', 'source', 'region', 'due_date', 
                         'info_session_date', 'url', 'amount_text', 'amount_krw', 
                         'stage', 'update_type', 'budget_band', 'allowed_uses', 'keywords']
        
        # 통합 시도
        combined_df = pd.DataFrame()
        if not biz_df.empty:
            biz_selected = biz_df[common_columns]
            combined_df = pd.concat([combined_df, biz_selected], ignore_index=True)
            print(f"biz2 선택된 컬럼: {list(biz_selected.columns)}")
        
        if not kstartup_df.empty:
            kstartup_selected = kstartup_df[common_columns]
            combined_df = pd.concat([combined_df, kstartup_selected], ignore_index=True)
            print(f"kstartup2 선택된 컬럼: {list(kstartup_selected.columns)}")
        
        print(f"통합 결과: {len(combined_df)}개 레코드")
        print(f"통합 컬럼: {list(combined_df.columns)}")
        
        if not combined_df.empty:
            print(f"샘플 데이터:")
            for idx, row in combined_df.head(3).iterrows():
                print(f"   {idx+1}. {row.get('title', 'N/A')} ({row.get('source', 'N/A')})")
        
    except Exception as e:
        print(f"❌ 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("🐛 announcements 데이터 구조 디버깅 시작")
    print("=" * 60)
    
    debug_announcements()
    test_announcements_merge()
    
    print("\n" + "=" * 60)
    print("✅ 디버깅 완료")

if __name__ == "__main__":
    main()

