"""
recommend_keyword 테이블에 recommendations_keyword_enhanced.csv 데이터를 저장하는 수정된 스크립트
"""
import pandas as pd
import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_to_recommend_keyword_fixed(supabase: Client, csv_path: str):
    """recommend_keyword 테이블에 CSV 데이터를 저장 (데이터 타입 수정)"""
    try:
        # CSV 파일 읽기 (처음 10행으로 테스트)
        logger.info(f"CSV 파일 읽기 시작: {csv_path}")
        
        df = pd.read_csv(csv_path, nrows=10)
        
        logger.info(f"CSV 컬럼: {list(df.columns)}")
        logger.info(f"읽은 행 수: {len(df)}")
        
        # NaN 값을 None으로 변환
        df = df.where(pd.notnull(df), None)
        
        # 데이터를 딕셔너리 리스트로 변환
        data = df.to_dict('records')
        
        # 각 레코드에서 NaN 값을 None으로 변환하고 데이터 타입 수정
        for record in data:
            for key, value in record.items():
                if pd.isna(value) or value == float('inf') or value == float('-inf'):
                    record[key] = None
                # 실수를 정수로 변환 (bigint 타입 컬럼용)
                elif key in ['kw_phrase_hit', 'kw_must_have_hits', 'kw_forbid_hit']:
                    if value is not None:
                        try:
                            record[key] = int(float(value))
                        except (ValueError, TypeError):
                            record[key] = 0
        
        # recommend_keyword 테이블에 맞춰서 매핑
        table_name = "recommend_keyword"
        
        # id 없이 데이터로 변환
        mapped_data = []
        for i, record in enumerate(data):
            mapped_record = {
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
        
        logger.info(f"테이블 '{table_name}'에 데이터 삽입 시도...")
        
        try:
            result = supabase.table(table_name).insert(mapped_data).execute()
            logger.info(f"성공적으로 {len(mapped_data)}행이 삽입되었습니다.")
            logger.info(f"삽입된 데이터 샘플: {result.data[:2] if result.data else 'None'}")
            
            # 이제 전체 데이터 업로드
            logger.info("전체 데이터 업로드를 시작합니다...")
            return upload_full_data_fixed(supabase, csv_path, table_name)
            
        except Exception as insert_error:
            logger.error(f"데이터 삽입 실패: {insert_error}")
            return False
        
    except Exception as e:
        logger.error(f"CSV 파일 처리 중 오류 발생: {e}")
        return False

def upload_full_data_fixed(supabase: Client, csv_path: str, table_name: str):
    """전체 CSV 데이터를 업로드 (데이터 타입 수정)"""
    try:
        logger.info(f"전체 CSV 데이터를 '{table_name}' 테이블에 업로드 시작...")
        
        chunk_size = 1000
        total_rows = 0
        
        for chunk_num, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size)):
            logger.info(f"청크 {chunk_num + 1} 처리 중... (행 수: {len(chunk)})")
            
            # NaN 값을 None으로 변환
            chunk = chunk.where(pd.notnull(chunk), None)
            
            # 데이터를 딕셔너리 리스트로 변환
            data = chunk.to_dict('records')
            
            # 각 레코드에서 NaN 값을 None으로 변환하고 데이터 타입 수정
            for record in data:
                for key, value in record.items():
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        record[key] = None
                    # 실수를 정수로 변환 (bigint 타입 컬럼용)
                    elif key in ['kw_phrase_hit', 'kw_must_have_hits', 'kw_forbid_hit']:
                        if value is not None:
                            try:
                                record[key] = int(float(value))
                            except (ValueError, TypeError):
                                record[key] = 0
            
            # id 없이 데이터로 변환
            mapped_data = []
            for i, record in enumerate(data):
                mapped_record = {
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
            result = supabase.table(table_name).insert(mapped_data).execute()
            total_rows += len(mapped_data)
            
            logger.info(f"청크 {chunk_num + 1} 완료: {len(mapped_data)}행 삽입 (총 {total_rows}행)")
        
        logger.info(f"전체 업로드 완료: 총 {total_rows}행이 '{table_name}' 테이블에 삽입되었습니다.")
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
    
    # recommend_keyword 테이블에 데이터 저장
    if upload_to_recommend_keyword_fixed(supabase, csv_path):
        logger.info("recommendations_keyword_enhanced 데이터 저장이 성공적으로 완료되었습니다.")
    else:
        logger.error("데이터 저장에 실패했습니다.")

if __name__ == "__main__":
    main()
