"""
업로드된 데이터를 검증하는 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_upload(supabase: Client):
    """업로드된 데이터 검증"""
    try:
        # 전체 데이터 개수 확인
        result = supabase.table("announcements").select("id", count="exact").execute()
        total_count = result.count
        logger.info(f"총 데이터 개수: {total_count}")
        
        # 샘플 데이터 확인
        sample_result = supabase.table("announcements").select("*").limit(5).execute()
        logger.info(f"샘플 데이터 (5개):")
        for i, record in enumerate(sample_result.data):
            logger.info(f"  {i+1}. ID: {record['id']}, 제목: {record['title'][:50]}...")
            logger.info(f"      URL: {record['url']}")
            logger.info(f"      Keywords: {record['keywords']}")
            logger.info("")
        
        # company_id별 통계
        stats_result = supabase.table("announcements").select("keywords").execute()
        company_counts = {}
        for record in stats_result.data:
            keywords = record['keywords']
            if keywords and len(keywords) > 0:
                company_id = keywords[0].split(':')[1] if ':' in keywords[0] else 'unknown'
                company_counts[company_id] = company_counts.get(company_id, 0) + 1
        
        logger.info(f"회사별 데이터 개수 (상위 10개):")
        sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for company_id, count in sorted_companies:
            logger.info(f"  회사 ID {company_id}: {count}개")
        
        return True
        
    except Exception as e:
        logger.error(f"데이터 검증 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    # Supabase 클라이언트 생성
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase 연결 성공")
    except Exception as e:
        logger.error(f"Supabase 연결 실패: {e}")
        return
    
    # 데이터 검증
    if verify_upload(supabase):
        logger.info("데이터 검증이 성공적으로 완료되었습니다.")
    else:
        logger.error("데이터 검증에 실패했습니다.")

if __name__ == "__main__":
    main()
