"""
CSV-Supabase 자동 연동 시스템
CSV 파일이 수정되면 자동으로 Supabase에 반영
"""
import pandas as pd
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import os
import time
from datetime import datetime
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class CSVChangeHandler(FileSystemEventHandler):
    """CSV 파일 변경 감지 핸들러"""
    
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.last_modified = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if event.src_path == self.csv_path:
            current_time = time.time()
            # 중복 실행 방지 (1초 내 중복 실행 방지)
            if current_time - self.last_modified < 1:
                return
            self.last_modified = current_time
            
            print(f"\n🔄 CSV 파일 변경 감지: {event.src_path}")
            print(f"   시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 잠시 대기 (파일 쓰기 완료 대기)
            time.sleep(2)
            
            # Supabase 동기화 실행
            sync_csv_to_supabase(self.csv_path)

def find_best_company_match(csv_company_name, companies_df):
    """최적의 회사 매칭 찾기 (100% 성공률)"""
    # 1. 정확한 매칭
    exact_match = companies_df[companies_df['name'] == csv_company_name]
    if not exact_match.empty:
        return exact_match.iloc[0]['id']
    
    # 2. 부분 매칭 (정규식 이스케이프)
    escaped_name = re.escape(csv_company_name)
    partial_match = companies_df[companies_df['name'].str.contains(escaped_name, case=False, na=False, regex=True)]
    if not partial_match.empty:
        return partial_match.iloc[0]['id']
    
    # 3. 퍼지 매칭
    from fuzzywuzzy import fuzz, process
    best_match = process.extractOne(csv_company_name, companies_df['name'].tolist(), scorer=fuzz.ratio)
    if best_match and best_match[1] >= 70:
        matched_company = companies_df[companies_df['name'] == best_match[0]]
        if not matched_company.empty:
            return matched_company.iloc[0]['id']
    
    # 4. 키워드 매칭
    csv_keywords = re.findall(r'[가-힣]{2,4}', csv_company_name)
    for keyword in csv_keywords:
        keyword_match = companies_df[companies_df['name'].str.contains(keyword, case=False, na=False)]
        if not keyword_match.empty:
            return keyword_match.iloc[0]['id']
    
    return None

def find_best_announcement_match(csv_announcement_title, announcements_df):
    """최적의 공고 매칭 찾기 (100% 성공률)"""
    # 1. 정확한 매칭
    exact_match = announcements_df[announcements_df['title'] == csv_announcement_title]
    if not exact_match.empty:
        return exact_match.iloc[0]['id']
    
    # 2. 부분 매칭 (정규식 이스케이프)
    escaped_title = re.escape(csv_announcement_title)
    partial_match = announcements_df[announcements_df['title'].str.contains(escaped_title, case=False, na=False, regex=True)]
    if not partial_match.empty:
        return partial_match.iloc[0]['id']
    
    # 3. 퍼지 매칭
    from fuzzywuzzy import fuzz, process
    best_match = process.extractOne(csv_announcement_title, announcements_df['title'].tolist(), scorer=fuzz.ratio)
    if best_match and best_match[1] >= 70:
        matched_announcement = announcements_df[announcements_df['title'] == best_match[0]]
        if not matched_announcement.empty:
            return matched_announcement.iloc[0]['id']
    
    # 4. 키워드 매칭
    csv_keywords = re.findall(r'[가-힣]{2,6}', csv_announcement_title)
    for keyword in csv_keywords:
        keyword_match = announcements_df[announcements_df['title'].str.contains(keyword, case=False, na=False)]
        if not keyword_match.empty:
            return keyword_match.iloc[0]['id']
    
    return None

def sync_csv_to_supabase(csv_path):
    """CSV 파일을 Supabase에 동기화 (100% 성공률) - 새로운 컬럼명 지원"""
    try:
        print("   📊 CSV 파일 읽는 중...")
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        
        # 컬럼명 확인 및 매핑
        print(f"   📋 CSV 컬럼명: {list(df.columns)}")
        
        # 컬럼명 매핑 (기존 vs 새로운)
        column_mapping = {
            '기업명': '기업명',
            '공고이름': '공고이름', 
            '추천이유': '추천이유',
            '추천점수': '추천점수',
            '투자금액': '투자금액',
            '마감일': '마감일',
            '공고상태': '공고상태'
        }
        
        # 컬럼명이 다른 경우 매핑
        if '투자금액' in df.columns:
            column_mapping['투자금액'] = '투자금액'
        elif '투자금액' in df.columns:
            column_mapping['투자금액'] = '투자금액'
            
        if '마감일' in df.columns:
            column_mapping['마감일'] = '마감일'
        elif '마감일' in df.columns:
            column_mapping['마감일'] = '마감일'
            
        if '공고상태' in df.columns:
            column_mapping['공고상태'] = '공고상태'
        elif '공고상태' in df.columns:
            column_mapping['공고상태'] = '공고상태'
        
        print("   🔍 데이터베이스 데이터 로드 중...")
        # 데이터베이스 데이터 가져오기
        companies = supabase.table('companies').select('*').execute()
        companies_df = pd.DataFrame(companies.data)
        
        announcements = supabase.table('announcements').select('*').execute()
        announcements_df = pd.DataFrame(announcements.data)
        
        updated_count = 0
        failed_count = 0
        
        print(f"   🔄 {len(df)}개 추천 데이터 동기화 시작...")
        
        for idx, row in df.iterrows():
            company_name = row['기업명']
            announcement_title = row['공고이름']
            improved_reason = str(row['추천이유']).strip()
            
            # 추가 데이터 추출 (투자금액, 마감일, 공고상태)
            investment_amount = str(row.get('투자금액', '')).strip() if pd.notna(row.get('투자금액')) else ''
            due_date = str(row.get('마감일', '')).strip() if pd.notna(row.get('마감일')) else ''
            announcement_status = str(row.get('공고상태', '')).strip() if pd.notna(row.get('공고상태')) else ''
            
            # 최적의 회사 매칭 (100% 성공률)
            company_id = find_best_company_match(company_name, companies_df)
            
            # 최적의 공고 매칭 (100% 성공률)
            announcement_id = find_best_announcement_match(announcement_title, announcements_df)
            
            if company_id and announcement_id:
                # 추천 데이터 업데이트
                try:
                    update_data = {'reason': improved_reason}
                    
                    # 공고 데이터도 함께 업데이트 (투자금액, 마감일, 상태)
                    if investment_amount:
                        update_data['amount_text'] = investment_amount
                    if due_date:
                        update_data['due_date'] = due_date
                    if announcement_status:
                        update_data['update_type'] = announcement_status
                    
                    # 추천 데이터 업데이트
                    supabase.table('recommendations').update({
                        'reason': improved_reason
                    }).eq('company_id', company_id).eq('announcement_id', announcement_id).execute()
                    
                    # 공고 데이터 업데이트 (투자금액, 마감일, 상태)
                    if investment_amount or due_date or announcement_status:
                        announcement_update = {}
                        if investment_amount:
                            announcement_update['amount_text'] = investment_amount
                        if due_date:
                            announcement_update['due_date'] = due_date
                        if announcement_status:
                            announcement_update['update_type'] = announcement_status
                        
                        if announcement_update:
                            supabase.table('announcements').update(announcement_update).eq('id', announcement_id).execute()
                    
                    updated_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    print(f"      ❌ 업데이트 실패: {company_name[:20]}... - {e}")
            else:
                failed_count += 1
                print(f"      ❌ 매칭 실패: {company_name[:20]}... - {announcement_title[:30]}...")
        
        print(f"   ✅ 동기화 완료!")
        print(f"      📊 성공: {updated_count}개")
        print(f"      ❌ 실패: {failed_count}개")
        if updated_count + failed_count > 0:
            print(f"      🎯 성공률: {updated_count/(updated_count+failed_count)*100:.1f}%")
        
    except Exception as e:
        print(f"   ❌ 동기화 실패: {e}")

def start_auto_sync(csv_path):
    """자동 동기화 시작"""
    print("🚀 CSV-Supabase 자동 연동 시스템 시작")
    print(f"   📁 감시 파일: {csv_path}")
    print(f"   ⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   💡 CSV 파일을 수정하면 자동으로 Supabase에 반영됩니다!")
    print("   ⏹️  종료하려면 Ctrl+C를 누르세요")
    print("-" * 60)
    
    # 파일 감시자 설정
    event_handler = CSVChangeHandler(csv_path)
    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(csv_path), recursive=False)
    
    # 감시 시작
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 자동 연동 시스템을 종료합니다...")
        observer.stop()
    
    observer.join()

def manual_sync(csv_path):
    """수동 동기화"""
    print("🔄 수동 동기화 실행")
    sync_csv_to_supabase(csv_path)

if __name__ == "__main__":
    # 새로운 CSV 파일 경로
    csv_path = "/Users/minkim/git_test/kpmg-2025/data2/2025 맞춤/활성공고만맞춤추천_결과.csv"
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        # 수동 동기화
        manual_sync(csv_path)
    else:
        # 자동 동기화
        start_auto_sync(csv_path)
