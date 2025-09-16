"""
강력한 동기화 - 모든 투자금액, 마감일, 상태 데이터 강제 업데이트
"""
import pandas as pd
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import re

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def force_sync():
    """강력한 동기화 실행"""
    print("🚀 강력한 동기화 시작")
    
    # CSV 파일 읽기
    csv_path = "/Users/minkim/git_test/kpmg-2025/data2/2025 맞춤/활성공고만맞춤추천_결과.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"📊 CSV 데이터: {len(df)}개")
    print(f"📋 CSV 컬럼: {list(df.columns)}")
    
    # 데이터베이스 데이터 가져오기
    companies = supabase.table('companies').select('*').execute()
    companies_df = pd.DataFrame(companies.data)
    
    announcements = supabase.table('announcements').select('*').execute()
    announcements_df = pd.DataFrame(announcements.data)
    
    print(f"📊 DB 회사: {len(companies_df)}개")
    print(f"📊 DB 공고: {len(announcements_df)}개")
    
    updated_recommendations = 0
    updated_announcements = 0
    
    print("🔄 강력한 동기화 시작...")
    
    for idx, row in df.iterrows():
        company_name = row['기업명']
        announcement_title = row['공고이름']
        improved_reason = str(row['추천이유']).strip()
        
        # 투자금액, 마감일, 상태 추출
        investment_amount = str(row.get('투자금액', '')).strip() if pd.notna(row.get('투자금액')) else ''
        due_date = str(row.get('마감일', '')).strip() if pd.notna(row.get('마감일')) else ''
        announcement_status = str(row.get('공고상태', '')).strip() if pd.notna(row.get('공고상태')) else ''
        
        print(f"   처리 중: {company_name[:30]}... | 투자금액: {investment_amount} | 마감일: {due_date} | 상태: {announcement_status}")
        
        # 회사 매칭 (더 유연한 매칭)
        company_match = None
        for _, db_company in companies_df.iterrows():
            if company_name in db_company['name'] or db_company['name'] in company_name:
                company_match = db_company
                break
        
        # 공고 매칭 (더 유연한 매칭)
        announcement_match = None
        for _, db_announcement in announcements_df.iterrows():
            if announcement_title in db_announcement['title'] or db_announcement['title'] in announcement_title:
                announcement_match = db_announcement
                break
        
        if company_match is not None and announcement_match is not None:
            company_id = company_match['id']
            announcement_id = announcement_match['id']
            
            try:
                # 추천 이유 업데이트
                supabase.table('recommendations').update({
                    'reason': improved_reason
                }).eq('company_id', company_id).eq('announcement_id', announcement_id).execute()
                updated_recommendations += 1
                
                # 공고 데이터 강제 업데이트
                announcement_update = {}
                if investment_amount and investment_amount != 'None' and investment_amount != '':
                    announcement_update['amount_text'] = investment_amount
                if due_date and due_date != 'None' and due_date != '':
                    announcement_update['due_date'] = due_date
                if announcement_status and announcement_status != 'None' and announcement_status != '':
                    announcement_update['update_type'] = announcement_status
                
                if announcement_update:
                    supabase.table('announcements').update(announcement_update).eq('id', announcement_id).execute()
                    updated_announcements += 1
                    print(f"      ✅ 업데이트: {announcement_update}")
                
            except Exception as e:
                print(f"      ❌ 업데이트 실패: {e}")
        else:
            print(f"      ❌ 매칭 실패: 회사={company_match is not None}, 공고={announcement_match is not None}")
    
    print(f"✅ 강력한 동기화 완료!")
    print(f"   📊 추천 데이터 업데이트: {updated_recommendations}개")
    print(f"   📊 공고 데이터 업데이트: {updated_announcements}개")

if __name__ == "__main__":
    force_sync()
