"""
새로운 회사 ID에 맞게 추천 데이터 업데이트
"""
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import random
from datetime import datetime, timedelta

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def update_recommendations():
    """새로운 회사 ID에 맞게 추천 데이터 업데이트"""
    print("추천 데이터 업데이트 시작...")
    
    # 기존 추천 데이터 삭제
    print("기존 추천 데이터 삭제 중...")
    supabase.table('recommendations').delete().neq('id', 0).execute()
    
    # 회사 데이터 가져오기
    companies = supabase.table('companies').select('*').execute()
    if not companies.data:
        print("회사 데이터가 없습니다.")
        return
    
    # 공고 데이터 가져오기
    announcements = supabase.table('announcements').select('*').execute()
    if not announcements.data:
        print("공고 데이터가 없습니다.")
        return
    
    print(f"회사 {len(companies.data)}개, 공고 {len(announcements.data)}개")
    
    # 각 회사에 대해 랜덤한 추천 생성
    recommendations_data = []
    
    for company in companies.data:
        # 각 회사당 3-8개의 추천 생성
        num_recommendations = random.randint(3, 8)
        selected_announcements = random.sample(announcements.data, min(num_recommendations, len(announcements.data)))
        
        for rank, announcement in enumerate(selected_announcements, 1):
            # 랜덤한 추천 점수 (70-95)
            score = random.uniform(70, 95)
            
            # 랜덤한 날짜 생성
            start_date = datetime.now() + timedelta(days=random.randint(-30, 30))
            end_date = start_date + timedelta(days=random.randint(30, 90))
            
            # 남은 기간 계산
            remaining_days = (end_date - datetime.now()).days
            
            recommendation_data = {
                'company_id': company['id'],
                'announcement_id': announcement['id'],
                'rank': rank,
                'score': round(score, 2),
                'reason': f"{company['name']} 기업에 적합한 {announcement['title']} 공고입니다.",
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'remaining_days': remaining_days,
                'amount_krw': announcement.get('amount_krw'),
                'amount_text': announcement.get('amount_text', ''),
                'allowed_uses': [],
                'status': '활성' if remaining_days > 0 else '마감',
                'year': 2025,
                'month': random.randint(1, 12)
            }
            recommendations_data.append(recommendation_data)
    
    # Supabase에 삽입
    if recommendations_data:
        try:
            # 배치로 삽입
            batch_size = 100
            for i in range(0, len(recommendations_data), batch_size):
                batch = recommendations_data[i:i+batch_size]
                result = supabase.table('recommendations').insert(batch).execute()
                print(f"추천 데이터 {len(batch)}개 삽입 완료")
            print(f"총 추천 데이터 {len(recommendations_data)}개 삽입 완료")
        except Exception as e:
            print(f"추천 데이터 삽입 실패: {e}")
    else:
        print("추천 데이터가 없습니다.")

if __name__ == "__main__":
    update_recommendations()
