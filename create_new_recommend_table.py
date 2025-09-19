"""
새로운 recommend_keyword4 테이블을 생성하고 CSV 데이터를 업로드하는 스크립트
"""
import pandas as pd
import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_new_recommend_table(supabase: Client, csv_path: str):
    """새로운 recommend_keyword4 테이블을 생성하고 CSV 데이터를 업로드"""
    try:
        # CSV 파일 읽기 (처음 10행만으로 테스트)
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
        
        # 새로운 테이블명으로 시도
        table_name = "recommendations_keyword_enhanced"
        
        # id를 포함한 데이터로 변환
        mapped_data = []
        for i, record in enumerate(data):
            mapped_record = {
                "id": i + 1,
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
            return True
            
        except Exception as insert_error:
            logger.error(f"테이블 '{table_name}' 삽입 실패: {insert_error}")
            
            # 기존 recommend_keyword4 테이블에 데이터 삽입 시도
            logger.info("기존 recommend_keyword4 테이블에 데이터 삽입 시도...")
            
            try:
                # id만 포함한 데이터로 시도
                id_only_data = [{"id": i + 1} for i in range(len(data))]
                result = supabase.table("recommend_keyword4").insert(id_only_data).execute()
                logger.info(f"id만으로 {len(id_only_data)}행이 삽입되었습니다.")
                
                # 이제 다른 컬럼들을 추가해보기
                logger.info("다른 컬럼들을 추가해보기...")
                
                # company_id 컬럼 추가 시도
                try:
                    company_data = []
                    for i, record in enumerate(data):
                        company_record = {
                            "id": i + 1,
                            "company_id": record.get("company_id")
                        }
                        company_data.append(company_record)
                    
                    result = supabase.table("recommend_keyword4").insert(company_data).execute()
                    logger.info(f"company_id 컬럼 추가 성공: {len(company_data)}행")
                    
                except Exception as company_error:
                    logger.error(f"company_id 컬럼 추가 실패: {company_error}")
                
                return True
                
            except Exception as existing_error:
                logger.error(f"기존 테이블 삽입도 실패: {existing_error}")
                return False
        
    except Exception as e:
        logger.error(f"CSV 파일 처리 중 오류 발생: {e}")
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
    
    # 새로운 recommend_keyword4 테이블 생성 및 데이터 삽입
    if create_new_recommend_table(supabase, csv_path):
        logger.info("recommend_keyword4 테이블 생성 및 데이터 업로드가 성공적으로 완료되었습니다.")
    else:
        logger.error("recommend_keyword4 테이블 생성 및 데이터 업로드에 실패했습니다.")

if __name__ == "__main__":
    main()
