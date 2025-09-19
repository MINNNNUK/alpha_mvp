"""
컬럼을 점진적으로 추가하면서 recommend_keyword4 테이블을 완성하는 스크립트
"""
import pandas as pd
import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_columns_gradually(supabase: Client, csv_path: str):
    """컬럼을 점진적으로 추가하면서 테이블을 완성"""
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
        
        # 컬럼을 점진적으로 추가
        columns_to_add = [
            ['id', 'company_id'],
            ['id', 'company_id', 'company_name'],
            ['id', 'company_id', 'company_name', 'program_id'],
            ['id', 'company_id', 'company_name', 'program_id', 'title'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type', 'apply_start'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type', 'apply_start', 'apply_end'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type', 'apply_start', 'apply_end', 'kw_intersection'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type', 'apply_start', 'apply_end', 'kw_intersection', 'kw_tfidf'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type', 'apply_start', 'apply_end', 'kw_intersection', 'kw_tfidf', 'kw_bm25'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type', 'apply_start', 'apply_end', 'kw_intersection', 'kw_tfidf', 'kw_bm25', 'kw_phrase_hit'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type', 'apply_start', 'apply_end', 'kw_intersection', 'kw_tfidf', 'kw_bm25', 'kw_phrase_hit', 'kw_must_have_hits'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type', 'apply_start', 'apply_end', 'kw_intersection', 'kw_tfidf', 'kw_bm25', 'kw_phrase_hit', 'kw_must_have_hits', 'kw_forbid_hit'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type', 'apply_start', 'apply_end', 'kw_intersection', 'kw_tfidf', 'kw_bm25', 'kw_phrase_hit', 'kw_must_have_hits', 'kw_forbid_hit', 'kw_gate'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type', 'apply_start', 'apply_end', 'kw_intersection', 'kw_tfidf', 'kw_bm25', 'kw_phrase_hit', 'kw_must_have_hits', 'kw_forbid_hit', 'kw_gate', 'kw_reason'],
            ['id', 'company_id', 'company_name', 'program_id', 'title', 'url', 'priority_type', 'apply_start', 'apply_end', 'kw_intersection', 'kw_tfidf', 'kw_bm25', 'kw_phrase_hit', 'kw_must_have_hits', 'kw_forbid_hit', 'kw_gate', 'kw_reason', 'keyword_points']
        ]
        
        table_name = "recommend_keyword4"
        
        for i, columns in enumerate(columns_to_add):
            try:
                logger.info(f"컬럼 {columns}로 삽입 시도...")
                
                filtered_data = []
                for j, record in enumerate(data):
                    filtered_record = {col: record.get(col) for col in columns if col in record}
                    filtered_record['id'] = j + 1  # id는 항상 포함
                    filtered_data.append(filtered_record)
                
                result = supabase.table(table_name).insert(filtered_data).execute()
                logger.info(f"성공! 컬럼 {columns}로 {len(filtered_data)}행이 삽입되었습니다.")
                
                # 마지막 컬럼까지 성공하면 전체 데이터 업로드
                if i == len(columns_to_add) - 1:
                    logger.info("모든 컬럼이 성공했습니다. 전체 데이터 업로드를 시작합니다...")
                    return upload_full_data(supabase, csv_path)
                
            except Exception as col_error:
                logger.error(f"컬럼 {columns} 삽입 실패: {col_error}")
                # 이전 성공한 컬럼으로 계속 진행
                continue
        
        logger.error("모든 컬럼 조합으로 삽입 실패")
        return False
        
    except Exception as e:
        logger.error(f"CSV 파일 처리 중 오류 발생: {e}")
        return False

def upload_full_data(supabase: Client, csv_path: str):
    """전체 CSV 데이터를 업로드"""
    try:
        logger.info("전체 CSV 데이터 업로드 시작...")
        
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
            
            # id를 포함한 데이터로 변환
            mapped_data = []
            for i, record in enumerate(data):
                mapped_record = {
                    "id": total_rows + i + 1,
                    "company_id": record.get("company_id"),
                    "company_name": record.get("company_name"),
                    "program_id": record.get("program_id"),
                    "title": record.get("title"),
                    "priority_type": record.get("priority_type"),
                    "apply_start": record.get("apply_start"),
                    "apply_end": record.get("apply_end"),
                    "url": record.get("url"),
                    "kw_intersection": record.get("kw_intersection"),
                    "kw_tfidf": record.get("kw_tfidf"),
                    "kw_bm25": record.get("kw_bm25"),
                    "kw_phrase_hit": record.get("kw_phrase_hit"),
                    "kw_must_have_hits": record.get("kw_must_have_hits"),
                    "kw_forbid_hit": record.get("kw_forbid_hit"),
                    "kw_gate": record.get("kw_gate"),
                    "kw_reason": record.get("kw_reason"),
                    "keyword_points": record.get("keyword_points")
                }
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
    
    # 컬럼을 점진적으로 추가하면서 테이블 완성
    if add_columns_gradually(supabase, csv_path):
        logger.info("recommend_keyword4 테이블 생성 및 전체 데이터 업로드가 성공적으로 완료되었습니다.")
    else:
        logger.error("recommend_keyword4 테이블 생성 및 데이터 업로드에 실패했습니다.")

if __name__ == "__main__":
    main()
