"""
recommend_keyword 관련 테이블들을 확인하는 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_recommend_keyword_tables(supabase: Client):
    """recommend_keyword 관련 테이블들 확인"""
    try:
        # recommend_keyword 관련 가능한 테이블명들
        keyword_tables = [
            "recommend_keyword",
            "recommend_keyword1",
            "recommend_keyword2", 
            "recommend_keyword3",
            "recommend_keyword4",
            "recommend_keyword5",
            "recommendations_keyword",
            "recommendations_keyword_enhanced",
            "keyword_recommendations",
            "keyword_recommend",
            "recommend_keywords"
        ]
        
        found_tables = []
        
        for table_name in keyword_tables:
            try:
                result = supabase.table(table_name).select("*").limit(1).execute()
                logger.info(f"✅ 테이블 '{table_name}' 사용 가능")
                found_tables.append(table_name)
                
                # 테이블 구조 확인
                if result.data:
                    logger.info(f"   컬럼: {list(result.data[0].keys())}")
                    logger.info(f"   샘플 데이터: {result.data[0]}")
                else:
                    logger.info(f"   테이블이 비어있음")
                    
            except Exception as e:
                logger.info(f"❌ 테이블 '{table_name}' 사용 불가: {e}")
                continue
        
        logger.info(f"\n찾은 recommend_keyword 관련 테이블: {found_tables}")
        return found_tables
        
    except Exception as e:
        logger.error(f"테이블 확인 중 오류 발생: {e}")
        return []

def main():
    """메인 함수"""
    # Supabase 클라이언트 생성
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase 연결 성공")
    except Exception as e:
        logger.error(f"Supabase 연결 실패: {e}")
        return
    
    # recommend_keyword 관련 테이블 확인
    found_tables = check_recommend_keyword_tables(supabase)
    
    if found_tables:
        logger.info(f"\n총 {len(found_tables)}개의 recommend_keyword 관련 테이블을 찾았습니다.")
    else:
        logger.info("recommend_keyword 관련 테이블을 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
