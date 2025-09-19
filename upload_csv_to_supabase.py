"""
CSV 파일을 Supabase 테이블로 업로드하는 스크립트
"""
import pandas as pd
import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(supabase: Client, table_name: str) -> bool:
    """테이블이 존재하는지 확인"""
    try:
        # 테이블 정보 조회 시도
        result = supabase.table(table_name).select("*").limit(1).execute()
        logger.info(f"테이블 '{table_name}'이 존재합니다.")
        return True
    except Exception as e:
        logger.info(f"테이블 '{table_name}'이 존재하지 않습니다: {e}")
        return False

def create_table_from_csv(supabase: Client, csv_path: str, table_name: str):
    """CSV 파일을 읽어서 테이블 생성 및 데이터 삽입"""
    try:
        # CSV 파일 읽기 (처음 몇 줄만 읽어서 구조 파악)
        logger.info(f"CSV 파일 읽기 시작: {csv_path}")
        
        # 파일 크기가 크므로 청크 단위로 읽기
        chunk_size = 1000
        first_chunk = pd.read_csv(csv_path, nrows=chunk_size)
        
        logger.info(f"CSV 컬럼: {list(first_chunk.columns)}")
        logger.info(f"첫 번째 청크 크기: {len(first_chunk)}")
        
        # 전체 파일을 청크 단위로 읽어서 데이터 삽입
        total_rows = 0
        for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
            # NaN 값을 None으로 변환하고, 무한대 값도 처리
            chunk = chunk.replace([float('inf'), float('-inf')], None)
            chunk = chunk.where(pd.notnull(chunk), None)
            
            # 데이터를 딕셔너리 리스트로 변환
            data = chunk.to_dict('records')
            
            # 각 레코드에서 NaN 값을 None으로 변환
            for record in data:
                for key, value in record.items():
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        record[key] = None
            
            # Supabase에 데이터 삽입
            result = supabase.table(table_name).insert(data).execute()
            total_rows += len(data)
            
            logger.info(f"삽입된 행 수: {total_rows}")
        
        logger.info(f"총 {total_rows}행이 성공적으로 삽입되었습니다.")
        return True
        
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
    
    # 1. 테이블 존재 확인
    if check_table_exists(supabase, table_name):
        logger.info(f"테이블 '{table_name}'이 이미 존재합니다.")
        
        # 기존 테이블 데이터 삭제
        try:
            # 테이블 삭제 (Supabase에서는 직접 삭제할 수 없으므로 데이터만 삭제)
            supabase.table(table_name).delete().neq('id', 0).execute()
            logger.info("기존 테이블 데이터 삭제 완료")
        except Exception as e:
            logger.warning(f"기존 데이터 삭제 중 오류: {e}")
    else:
        logger.info(f"테이블 '{table_name}'이 존재하지 않습니다. 새로 생성합니다.")
    
    # 2. CSV 파일 확인
    if not os.path.exists(csv_path):
        logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
        return
    
    logger.info(f"CSV 파일 확인 완료: {csv_path}")
    
    # 3. CSV 파일을 테이블로 업로드
    if create_table_from_csv(supabase, csv_path, table_name):
        logger.info("CSV 파일 업로드가 성공적으로 완료되었습니다.")
    else:
        logger.error("CSV 파일 업로드에 실패했습니다.")

if __name__ == "__main__":
    main()
