"""
데이터 완성도 검증 스크립트
"""
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import pandas as pd

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_data_completeness():
    """데이터 완성도 검증"""
    print("데이터 완성도 검증 시작...")
    
    # 회사 데이터 확인
    companies = supabase.table('companies').select('*').execute()
    print(f"회사 수: {len(companies.data)}")
    
    # 공고 데이터 확인
    announcements = supabase.table('announcements').select('*').execute()
    print(f"공고 수: {len(announcements.data)}")
    
    # 추천 데이터 확인
    recommendations = supabase.table('recommendations').select('*').execute()
    print(f"추천 수: {len(recommendations.data)}")
    
    # 조인 테스트
    print("\n=== 조인 테스트 ===")
    recommendations_df = pd.DataFrame(recommendations.data)
    announcements_df = pd.DataFrame(announcements.data)
    
    if not recommendations_df.empty and not announcements_df.empty:
        merged_df = recommendations_df.merge(
            announcements_df, 
            left_on='announcement_id', 
            right_on='id', 
            how='inner',
            suffixes=('', '_ann')
        )
        
        print(f"조인 후 데이터 수: {len(merged_df)}")
        
        # 빈칸 확인
        print("\n=== 빈칸 확인 ===")
        for col in ['title', 'agency', 'amount_text']:
            if col in merged_df.columns:
                empty_count = merged_df[col].isna().sum() + (merged_df[col] == '').sum()
                print(f"{col}: {empty_count}개 빈칸")
            else:
                print(f"{col}: 컬럼 없음")
        
        # 샘플 데이터 출력
        print("\n=== 샘플 데이터 ===")
        if not merged_df.empty:
            sample_cols = ['rank', 'score', 'title', 'agency', 'amount_text', 'end_date', 'status']
            available_cols = [col for col in sample_cols if col in merged_df.columns]
            print(merged_df[available_cols].head(3).to_string())
    else:
        print("데이터가 없습니다.")

if __name__ == "__main__":
    verify_data_completeness()
