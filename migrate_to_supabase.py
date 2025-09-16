"""
데이터를 Supabase로 마이그레이션하는 스크립트
"""
import os
import pandas as pd
import json
from supabase import create_client, Client
from datetime import datetime
import re
from typing import List, Dict, Any

# Supabase 설정
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 데이터 경로 (현재 스크립트 위치 기준)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(SCRIPT_DIR, "data2")
ALPHA_COMPANIES_PATH = os.path.join(DATA_ROOT, "alpha_companies.csv")
LLM_MATCHES_ALL = os.path.join(DATA_ROOT, "2025 맞춤", "전체월포함맞춤추천_결과.csv")
LLM_MATCHES_ACTIVE = os.path.join(DATA_ROOT, "2025 맞춤", "활성공고만맞춤추천_결과.csv")
COLLECTED_DATA_PATH = os.path.join(DATA_ROOT, "collected_data")
COLLECTED_DATA_BIZ_PATH = os.path.join(DATA_ROOT, "collected_data_biz")

def parse_amount(amount_str: str) -> tuple[int | None, str]:
    """금액 문자열 파싱"""
    if pd.isna(amount_str) or amount_str == '':
        return None, str(amount_str) if not pd.isna(amount_str) else ''
    
    amount_str = str(amount_str).strip()
    original_text = amount_str
    
    # 금액 패턴
    amount_patterns = [
        r'(\d+(?:,\d{3})*)\s*(억|천만|만|원)',
        r'최대\s*(\d+(?:,\d{3})*)\s*(억|천만|만|원)',
        r'(\d+(?:,\d{3})*)\s*(억|천만|만|원)\s*이내',
        r'(\d+(?:,\d{3})*)\s*(억|천만|만|원)\s*이하'
    ]
    
    amount_units = {
        '억': 100_000_000,
        '천만': 10_000_000,
        '만': 10_000,
        '원': 1
    }
    
    for pattern in amount_patterns:
        match = re.search(pattern, amount_str)
        if match:
            groups = match.groups()
            if len(groups) >= 2:
                try:
                    amount_num = int(groups[0].replace(',', ''))
                    unit = groups[1]
                    
                    if unit in amount_units:
                        total_amount = amount_num * amount_units[unit]
                        return total_amount, original_text
                except:
                    continue
    
    return None, original_text

def parse_date(date_str: str) -> str | None:
    """날짜 문자열 파싱"""
    if pd.isna(date_str) or date_str == '':
        return None
    
    date_str = str(date_str).strip()
    
    # 날짜 패턴
    date_patterns = [
        r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})',
        r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',
        r'(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})',
        r'(\d{1,2})월\s*(\d{1,2})일\s*(\d{4})년'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, date_str)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                try:
                    # 년-월-일 순서 확인
                    if len(groups[0]) == 4:  # YYYY-MM-DD
                        year, month, day = groups
                    else:  # MM-DD-YYYY
                        month, day, year = groups
                    
                    parsed_date = datetime(int(year), int(month), int(day))
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
    
    return None

def migrate_companies():
    """회사 데이터 마이그레이션"""
    print("회사 데이터 마이그레이션 시작...")
    
    if not os.path.exists(ALPHA_COMPANIES_PATH):
        print(f"파일을 찾을 수 없습니다: {ALPHA_COMPANIES_PATH}")
        return
    
    df = pd.read_csv(ALPHA_COMPANIES_PATH)
    
    companies_data = []
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
        
        company_data = {
            'name': str(row['주업종 (사업자등록증 상)']) if pd.notna(row.get('주업종 (사업자등록증 상)')) else f"회사_{idx+1}",
            'business_type': str(row['기업형태']) if pd.notna(row.get('기업형태')) else '법인',
            'region': str(row['소재지']) if pd.notna(row.get('소재지')) else '',
            'years': years,
            'stage': stage,
            'industry': str(row['주요 산업']) if pd.notna(row.get('주요 산업')) else '',
            'keywords': keywords,
            'preferred_uses': [],
            'preferred_budget': '중간'
        }
        companies_data.append(company_data)
    
    # Supabase에 삽입
    try:
        result = supabase.table('companies').insert(companies_data).execute()
        print(f"회사 데이터 {len(companies_data)}개 삽입 완료")
    except Exception as e:
        print(f"회사 데이터 삽입 실패: {e}")

def migrate_announcements():
    """공고 데이터 마이그레이션"""
    print("공고 데이터 마이그레이션 시작...")
    
    announcements_data = []
    announcement_ids = set()
    
    # collected_data 폴더의 CSV 파일들 처리
    if os.path.exists(COLLECTED_DATA_PATH):
        import glob
        csv_files = glob.glob(os.path.join(COLLECTED_DATA_PATH, "*.csv"))
        for file in csv_files:
            try:
                df = pd.read_csv(file)
                for idx, row in df.iterrows():
                    announcement_id = str(row.get('공고번호', f"KS-{idx}"))
                    if announcement_id in announcement_ids:
                        continue
                    announcement_ids.add(announcement_id)
                    
                    # 금액 파싱
                    amount_krw, amount_text = parse_amount(str(row.get('지원금액', '')))
                    
                    # 날짜 파싱
                    due_date = parse_date(str(row.get('접수종료일', '')))
                    start_date = parse_date(str(row.get('접수시작일', '')))
                    
                    announcement_data = {
                        'id': announcement_id,
                        'title': str(row.get('사업공고명', '')),
                        'agency': str(row.get('공고기관명', '')),
                        'source': 'K-Startup',
                        'region': str(row.get('지원지역', '')),
                        'stage': str(row.get('사업경력', '')),
                        'due_date': due_date,
                        'info_session_date': start_date,
                        'amount_krw': amount_krw,
                        'amount_text': amount_text,
                        'allowed_uses': [],
                        'keywords': [],
                        'budget_band': '중간',
                        'update_type': '신규',
                        'url': str(row.get('상세페이지URL', ''))
                    }
                    announcements_data.append(announcement_data)
            except Exception as e:
                print(f"파일 처리 실패 {file}: {e}")
                continue
    
    # collected_data_biz 폴더의 CSV 파일들 처리
    if os.path.exists(COLLECTED_DATA_BIZ_PATH):
        csv_files = glob.glob(os.path.join(COLLECTED_DATA_BIZ_PATH, "*.csv"))
        for file in csv_files:
            try:
                df = pd.read_csv(file)
                for idx, row in df.iterrows():
                    announcement_id = str(row.get('공고번호', f"BIZ-{idx}"))
                    if announcement_id in announcement_ids:
                        continue
                    announcement_ids.add(announcement_id)
                    
                    # 금액 파싱
                    amount_krw, amount_text = parse_amount(str(row.get('지원금액', '')))
                    
                    # 날짜 파싱
                    due_date = parse_date(str(row.get('접수종료일', '')))
                    start_date = parse_date(str(row.get('접수시작일', '')))
                    
                    announcement_data = {
                        'id': announcement_id,
                        'title': str(row.get('사업공고명', '')),
                        'agency': str(row.get('공고기관명', '')),
                        'source': 'Bizinfo',
                        'region': str(row.get('지원지역', '')),
                        'stage': str(row.get('사업경력', '')),
                        'due_date': due_date,
                        'info_session_date': start_date,
                        'amount_krw': amount_krw,
                        'amount_text': amount_text,
                        'allowed_uses': [],
                        'keywords': [],
                        'budget_band': '중간',
                        'update_type': '신규',
                        'url': str(row.get('상세페이지URL', ''))
                    }
                    announcements_data.append(announcement_data)
            except Exception as e:
                print(f"파일 처리 실패 {file}: {e}")
                continue
    
    # Supabase에 삽입
    if announcements_data:
        try:
            # 배치로 삽입 (한 번에 1000개씩)
            batch_size = 1000
            for i in range(0, len(announcements_data), batch_size):
                batch = announcements_data[i:i+batch_size]
                result = supabase.table('announcements').insert(batch).execute()
                print(f"공고 데이터 {len(batch)}개 삽입 완료")
            print(f"총 공고 데이터 {len(announcements_data)}개 삽입 완료")
        except Exception as e:
            print(f"공고 데이터 삽입 실패: {e}")

def migrate_recommendations():
    """추천 결과 데이터 마이그레이션"""
    print("추천 결과 데이터 마이그레이션 시작...")
    
    # 회사 ID 매핑 생성
    companies_result = supabase.table('companies').select('id, name').execute()
    company_id_map = {row['name']: row['id'] for row in companies_result.data}
    
    recommendations_data = []
    
    # 전체 추천 결과 처리
    if os.path.exists(LLM_MATCHES_ALL):
        df = pd.read_csv(LLM_MATCHES_ALL)
        for idx, row in df.iterrows():
            company_name = str(row.get('기업명', ''))
            company_id = company_id_map.get(company_name)
            
            if not company_id:
                continue
            
            # 금액 파싱
            amount_krw, amount_text = parse_amount(str(row.get('투자금액', '')))
            
            # 날짜 파싱
            start_date = parse_date(str(row.get('모집일', '')))
            end_date = parse_date(str(row.get('마감일', '')))
            
            # 남은 기간 계산
            remaining_days = None
            if end_date:
                try:
                    due_date = datetime.strptime(end_date, '%Y-%m-%d')
                    remaining_days = (due_date - datetime.now()).days
                except:
                    pass
            
            recommendation_data = {
                'company_id': company_id,
                'announcement_id': f"REC-{idx}",
                'rank': int(row.get('추천순위', 0)),
                'score': float(row.get('추천점수', 0)),
                'reason': str(row.get('추천이유', '')),
                'start_date': start_date,
                'end_date': end_date,
                'remaining_days': remaining_days,
                'amount_krw': amount_krw,
                'amount_text': amount_text,
                'allowed_uses': [],
                'status': str(row.get('공고상태', '')),
                'year': int(row.get('공고연도', 2025)),
                'month': int(row.get('공고월', 1))
            }
            recommendations_data.append(recommendation_data)
    
    # Supabase에 삽입
    if recommendations_data:
        try:
            # 배치로 삽입
            batch_size = 1000
            for i in range(0, len(recommendations_data), batch_size):
                batch = recommendations_data[i:i+batch_size]
                result = supabase.table('recommendations').insert(batch).execute()
                print(f"추천 데이터 {len(batch)}개 삽입 완료")
            print(f"총 추천 데이터 {len(recommendations_data)}개 삽입 완료")
        except Exception as e:
            print(f"추천 데이터 삽입 실패: {e}")

def main():
    """메인 마이그레이션 함수"""
    print("Supabase 데이터 마이그레이션 시작...")
    
    try:
        # 기존 데이터 삭제 (순서 중요: 외래키 때문에)
        print("기존 데이터 삭제 중...")
        supabase.table('recommendations').delete().neq('id', 0).execute()
        supabase.table('notification_states').delete().neq('id', 0).execute()
        supabase.table('announcements').delete().neq('id', '').execute()
        supabase.table('companies').delete().neq('id', 0).execute()
        
        # 데이터 마이그레이션
        migrate_companies()
        migrate_announcements()
        migrate_recommendations()
        
        print("마이그레이션 완료!")
        
    except Exception as e:
        print(f"마이그레이션 실패: {e}")

if __name__ == "__main__":
    main()
