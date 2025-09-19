"""
recommend_keyword4 테이블에 CSV 컬럼들을 생성하는 스크립트
"""
import pandas as pd
import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_columns_for_recommend(supabase: Client, csv_path: str):
    """recommend_keyword4 테이블에 CSV 컬럼들을 생성"""
    try:
        # CSV 파일 읽기 (처음 5행만으로 컬럼 확인)
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
        
        # recommend_keyword4 테이블에 컬럼을 하나씩 추가
        table_name = "recommend_keyword4"
        
        # 컬럼을 하나씩 추가하면서 테스트
        columns_to_add = [
            'company_id',
            'company_name', 
            'program_id',
            'title',
            'priority_type',
            'apply_start',
            'apply_end',
            'url',
            'kw_intersection',
            'kw_tfidf',
            'kw_bm25',
            'kw_phrase_hit',
            'kw_must_have_hits',
            'kw_forbid_hit',
            'kw_gate',
            'kw_reason',
            'keyword_points'
        ]
        
        successful_columns = ['id']  # id는 이미 존재
        
        for column in columns_to_add:
            try:
                logger.info(f"컬럼 '{column}' 추가 시도...")
                
                # 해당 컬럼을 포함한 데이터 생성
                test_data = []
                for i, record in enumerate(data):
                    test_record = {
                        "id": i + 1,
                        column: record.get(column)
                    }
                    test_data.append(test_record)
                
                # Supabase에 데이터 삽입 시도
                result = supabase.table(table_name).insert(test_data).execute()
                
                logger.info(f"컬럼 '{column}' 추가 성공!")
                successful_columns.append(column)
                
            except Exception as col_error:
                logger.error(f"컬럼 '{column}' 추가 실패: {col_error}")
                continue
        
        logger.info(f"성공적으로 추가된 컬럼들: {successful_columns}")
        
        # 이제 모든 성공한 컬럼으로 전체 데이터 삽입 시도
        if len(successful_columns) > 1:  # id 외에 다른 컬럼이 있으면
            logger.info("성공한 컬럼들로 전체 데이터 삽입 시도...")
            return upload_full_data_with_columns(supabase, csv_path, successful_columns)
        else:
            logger.warning("추가된 컬럼이 없습니다.")
            return False
        
    except Exception as e:
        logger.error(f"컬럼 생성 중 오류 발생: {e}")
        return False

def upload_full_data_with_columns(supabase: Client, csv_path: str, columns):
    """성공한 컬럼들로 전체 데이터 업로드"""
    try:
        logger.info(f"컬럼 {columns}로 전체 데이터 업로드 시작...")
        
        chunk_size = 1000
        total_rows = 0
        
        for chunk_num, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size)):
            logger.info(f"청크 {chunk_num + 1} 처리 중... (행 수: {len(chunk)})")
            
            # NaN 값을 None으로 변환
            chunk = chunk.where(pd.notnull(chunk), None)
            
            # 데이터를 딕셔너리 리스트로 변환
            data = chunk.to_dict('records')
            
            # 각 레코드에서 NaN 값을 None으로 변환
            for record in data:
                for key, value in record.items():
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        record[key] = None
            
            # 성공한 컬럼들만 포함한 데이터로 변환
            mapped_data = []
            for i, record in enumerate(data):
                mapped_record = {}
                for col in columns:
                    if col == 'id':
                        mapped_record[col] = total_rows + i + 1
                    else:
                        mapped_record[col] = record.get(col)
                mapped_data.append(mapped_record)
            
            # Supabase에 데이터 삽입
            result = supabase.table("recommend_keyword4").insert(mapped_data).execute()
            total_rows += len(mapped_data)
            
            logger.info(f"청크 {chunk_num + 1} 완료: {len(mapped_data)}행 삽입 (총 {total_rows}행)")
        
        logger.info(f"전체 업로드 완료: 총 {total_rows}행이 삽입되었습니다.")
        return True
        
    except Exception as e:
        logger.error(f"전체 데이터 업로드 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    csv_path = "/Users/minkim/git_test/kpmg-2025/Version3/recommendations_keyword_enhanced.csv"
    
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
    
    # recommend_keyword4 테이블에 컬럼 생성 및 데이터 업로드
    if create_columns_for_recommend(supabase, csv_path):
        logger.info("recommend_keyword4 테이블 컬럼 생성 및 데이터 업로드가 성공적으로 완료되었습니다.")
    else:
        logger.error("recommend_keyword4 테이블 컬럼 생성 및 데이터 업로드에 실패했습니다.")

if __name__ == "__main__":
    main()
