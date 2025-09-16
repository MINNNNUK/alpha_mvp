"""
alpha_companies.csv의 사업아이템 한 줄 소개를 기준으로 회사 데이터 업데이트
"""
import pandas as pd
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def update_companies_from_csv():
    """CSV 파일의 사업아이템을 기준으로 회사 데이터 업데이트"""
    print("회사 데이터 업데이트 시작...")
    
    # CSV 파일 읽기
    csv_file = 'data2/alpha_companies.csv'
    df = pd.read_csv(csv_file)
    
    print(f"CSV 파일에서 {len(df)}개 회사 데이터 로드")
    
    # 기존 회사 데이터 가져오기
    companies_result = supabase.table('companies').select('*').execute()
    existing_companies = {company['id']: company for company in companies_result.data}
    
    print(f"Supabase에서 {len(existing_companies)}개 회사 데이터 로드")
    
    # 업데이트할 데이터 준비
    updates = []
    
    for idx, row in df.iterrows():
        # 업력 계산
        years = 0
        if pd.notna(row.get('설립연월일')) and row['설립연월일'] != '-':
            try:
                establish_date = datetime.strptime(str(row['설립연월일']), '%Y.%m.%d')
                years = (datetime.now() - establish_date).days // 365
            except:
                years = 0
        
        # 성장단계 추정
        stage = "예비"
        if years >= 3:
            stage = "성장"
        elif years >= 1:
            stage = "초기"
        
        # 키워드 추출
        keywords = []
        if pd.notna(row.get('특화분야')):
            keywords.append(str(row['특화분야']))
        if pd.notna(row.get('주요 산업')):
            keywords.append(str(row['주요 산업']))
        
        # 사업아이템 한 줄 소개를 회사명으로 사용
        business_item = str(row.get('사업아이템 한 줄 소개', ''))
        if pd.isna(business_item) or business_item == '':
            business_item = f"회사_{idx+1}"
        
        # 업데이트할 회사 데이터
        company_data = {
            'name': business_item,
            'business_type': str(row['기업형태']) if pd.notna(row.get('기업형태')) else '법인',
            'region': str(row['소재지']) if pd.notna(row.get('소재지')) else '',
            'years': years,
            'stage': stage,
            'industry': str(row['주요 산업']) if pd.notna(row.get('주요 산업')) else '',
            'keywords': keywords,
            'preferred_uses': [],
            'preferred_budget': '중간'
        }
        
        # 기존 회사 ID가 있으면 업데이트, 없으면 새로 생성
        if idx + 1 in existing_companies:
            # 기존 회사 업데이트
            company_id = idx + 1
            try:
                result = supabase.table('companies').update(company_data).eq('id', company_id).execute()
                print(f"회사 ID {company_id} 업데이트: {business_item}")
            except Exception as e:
                print(f"회사 ID {company_id} 업데이트 실패: {e}")
        else:
            # 새 회사 생성
            try:
                result = supabase.table('companies').insert(company_data).execute()
                print(f"새 회사 생성: {business_item}")
            except Exception as e:
                print(f"새 회사 생성 실패: {e}")
    
    print("회사 데이터 업데이트 완료!")

if __name__ == "__main__":
    update_companies_from_csv()
