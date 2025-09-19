"""
테이블을 수동으로 생성하고 데이터를 삽입하는 스크립트
"""
import pandas as pd
import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_table_manually(supabase: Client, csv_path: str, table_name: str):
    """테이블을 수동으로 생성하고 데이터 삽입"""
    try:
        # CSV 파일 읽기 (처음 5행만)
        logger.info(f"CSV 파일 읽기 시작: {csv_path}")
        
        df = pd.read_csv(csv_path, nrows=5)
        
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
        
        # 모든 컬럼을 포함한 데이터로 삽입 시도
        logger.info("모든 컬럼을 포함한 데이터 삽입 시도...")
        
        try:
            result = supabase.table(table_name).insert(data).execute()
            logger.info(f"성공적으로 {len(data)}행이 삽입되었습니다.")
            logger.info(f"삽입된 데이터: {result.data}")
            return True
            
        except Exception as insert_error:
            logger.error(f"전체 컬럼 삽입 실패: {insert_error}")
            
            # 컬럼을 하나씩 제거하면서 시도
            columns_to_try = [
                ['company_id', 'company_name', 'program_id', 'title'],
                ['company_id', 'company_name', 'title'],
                ['company_id', 'company_name'],
                ['company_id'],
                ['title']
            ]
            
            for columns in columns_to_try:
                try:
                    logger.info(f"컬럼 {columns}로 삽입 시도...")
                    filtered_data = []
                    
                    for record in data:
                        filtered_record = {col: record.get(col) for col in columns if col in record}
                        filtered_data.append(filtered_record)
                    
                    result = supabase.table(table_name).insert(filtered_data).execute()
                    logger.info(f"성공! 컬럼 {columns}로 {len(filtered_data)}행이 삽입되었습니다.")
                    logger.info(f"삽입된 데이터: {result.data}")
                    return True
                    
                except Exception as col_error:
                    logger.error(f"컬럼 {columns} 삽입 실패: {col_error}")
                    continue
            
            logger.error("모든 컬럼 조합으로 삽입 실패")
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
    
    # 테이블 생성 및 데이터 삽입
    if create_table_manually(supabase, csv_path, table_name):
        logger.info("CSV 파일 업로드가 성공적으로 완료되었습니다.")
    else:
        logger.error("CSV 파일 업로드에 실패했습니다.")

if __name__ == "__main__":
    main()
