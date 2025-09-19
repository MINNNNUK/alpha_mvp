"""
CSV 파일을 간단하게 업로드하는 스크립트
"""
import pandas as pd
import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_csv_simple(supabase: Client, csv_path: str, table_name: str):
    """CSV 파일을 간단하게 업로드"""
    try:
        # CSV 파일 읽기 (처음 10행만)
        logger.info(f"CSV 파일 읽기 시작: {csv_path}")
        
        df = pd.read_csv(csv_path, nrows=10)
        
        logger.info(f"CSV 컬럼: {list(df.columns)}")
        logger.info(f"읽은 행 수: {len(df)}")
        
        # NaN 값을 None으로 변환
        df = df.where(pd.notnull(df), None)
        
        # 데이터를 딕셔너리 리스트로 변환
        data = df.to_dict('records')
        
        # 각 레코드에서 NaN 값을 None으로 변환
        for record in data:
            for key, value in record.items():
                if pd.isna(value) or value == float('inf') or value == float('-inf'):
                    record[key] = None
        
        # 필요한 컬럼만 선택하여 삽입 시도
        # CSV의 모든 컬럼을 포함하되, 테이블에 없는 컬럼은 제외
        try:
            result = supabase.table(table_name).insert(data).execute()
            logger.info(f"성공적으로 {len(data)}행이 삽입되었습니다.")
            return True
        except Exception as insert_error:
            logger.error(f"데이터 삽입 실패: {insert_error}")
            
            # 컬럼별로 개별 삽입 시도
            logger.info("컬럼별 개별 삽입을 시도합니다...")
            
            # 기본 컬럼들만으로 시도
            basic_columns = ['company_id', 'company_name', 'program_id', 'title']
            basic_data = []
            
            for record in data:
                basic_record = {col: record.get(col) for col in basic_columns if col in record}
                basic_data.append(basic_record)
            
            try:
                result = supabase.table(table_name).insert(basic_data).execute()
                logger.info(f"기본 컬럼으로 {len(basic_data)}행이 삽입되었습니다.")
                return True
            except Exception as basic_error:
                logger.error(f"기본 컬럼 삽입도 실패: {basic_error}")
                return False
        
    except Exception as e:
        logger.error(f"CSV 파일 처리 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    csv_path = "/Users/minkim/git_test/kpmg-2025/Version3/recommendations_keyword_enhanced.csv"
    table_name = "recommend_keyword4"
    
    # Supabase 클라이언트 생성
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase 연결 성공")
    except Exception as e:
        logger.error(f"Supabase 연결 실패: {e}")
        return
    
    # CSV 파일 확인
    if not os.path.exists(csv_path):
        logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
        return
    
    logger.info(f"CSV 파일 확인 완료: {csv_path}")
    
    # CSV 파일 업로드
    if upload_csv_simple(supabase, csv_path, table_name):
        logger.info("CSV 파일 업로드가 성공적으로 완료되었습니다.")
    else:
        logger.error("CSV 파일 업로드에 실패했습니다.")

if __name__ == "__main__":
    main()