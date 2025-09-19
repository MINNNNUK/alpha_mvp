"""
announcements 테이블에 recommendations_keyword_enhanced.csv의 모든 데이터를 저장하는 스크립트
"""
import pandas as pd
import os
import json
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_to_announcements_with_full_data(supabase: Client, csv_path: str):
    """announcements 테이블에 recommendations_keyword_enhanced.csv의 모든 데이터를 저장"""
    try:
        # CSV 파일 읽기 (청크 단위로)
        logger.info(f"CSV 파일 읽기 시작: {csv_path}")
        
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
            
            # announcements 테이블에 맞춰서 매핑 (모든 recommendations_keyword_enhanced 데이터 포함)
            mapped_data = []
            for i, record in enumerate(data):
                # recommendations_keyword_enhanced의 모든 데이터를 JSON으로 저장
                recommend_data = {
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
                
                mapped_record = {
                    "id": total_rows + i + 1,
                    "title": record.get("title", ""),
                    "url": record.get("url", ""),
                    "keywords": [f"company_id:{record.get('company_id', '')}", f"program_id:{record.get('program_id', '')}"],
                    "agency": "K-Startup",
                    "source": "kstartup",
                    "region": "전국",
                    "stage": "예비창업",
                    "amount_text": "미정",
                    "budget_band": "소규모",
                    "update_type": "신규",
                    # recommendations_keyword_enhanced의 모든 데이터를 JSON으로 저장
                    "recommendations_data": json.dumps(recommend_data, ensure_ascii=False)
                }
                mapped_data.append(mapped_record)
            
            # Supabase에 데이터 삽입
            result = supabase.table("announcements").insert(mapped_data).execute()
            total_rows += len(mapped_data)
            
            logger.info(f"청크 {chunk_num + 1} 완료: {len(mapped_data)}행 삽입 (총 {total_rows}행)")
        
        logger.info(f"전체 업로드 완료: 총 {total_rows}행이 삽입되었습니다.")
        logger.info("recommendations_keyword_enhanced의 모든 데이터가 announcements 테이블의 'recommendations_data' 컬럼에 JSON 형태로 저장되었습니다.")
        return True
        
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
    
    # 기존 데이터 삭제
    try:
        supabase.table("announcements").delete().neq('id', 0).execute()
        logger.info("기존 announcements 데이터 삭제 완료")
    except Exception as e:
        logger.warning(f"기존 데이터 삭제 중 오류: {e}")
    
    # recommendations_keyword_enhanced 데이터를 announcements 테이블에 저장
    if upload_to_announcements_with_full_data(supabase, csv_path):
        logger.info("recommendations_keyword_enhanced 데이터 저장이 성공적으로 완료되었습니다.")
    else:
        logger.error("데이터 저장에 실패했습니다.")

if __name__ == "__main__":
    main()
