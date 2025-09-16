"""
Supabase 데이터 분석 스크립트
현재 데이터베이스의 상태와 연동 상황을 분석
"""
import pandas as pd
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import json
from datetime import datetime

def analyze_database():
    """데이터베이스 전체 분석"""
    print("🔍 Supabase 데이터베이스 분석 시작...")
    print("=" * 60)
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 1. 테이블별 데이터 현황
        print("\n📊 테이블별 데이터 현황")
        print("-" * 40)
        
        tables = {
            'companies': '회사 정보',
            'announcements': '공고 정보', 
            'recommendations': '추천 결과',
            'notification_states': '알림 상태',
            'alpha_companies': '알파 회사 (기존 고객)',
            'recommendations2': '추천 결과 2',
            'recommendations3_active': '활성 추천'
        }
        
        table_stats = {}
        
        for table_name, description in tables.items():
            try:
                result = supabase.table(table_name).select('*').execute()
                count = len(result.data)
                table_stats[table_name] = {
                    'count': count,
                    'description': description,
                    'data': result.data[:3] if count > 0 else []  # 샘플 3개
                }
                print(f"✅ {table_name:20} | {description:15} | 레코드 수: {count:4d}")
            except Exception as e:
                print(f"❌ {table_name:20} | {description:15} | 오류: {str(e)[:30]}")
                table_stats[table_name] = {'count': 0, 'description': description, 'data': []}
        
        # 2. 상세 데이터 분석
        print("\n🔍 상세 데이터 분석")
        print("-" * 40)
        
        # Companies 테이블 분석
        if table_stats.get('companies', {}).get('count', 0) > 0:
            print("\n📋 Companies 테이블 분석:")
            companies_data = table_stats['companies']['data']
            if companies_data:
                sample = companies_data[0]
                print(f"   컬럼: {list(sample.keys())}")
                print(f"   샘플 데이터: {json.dumps(sample, ensure_ascii=False, indent=2)}")
        
        # Announcements 테이블 분석
        if table_stats.get('announcements', {}).get('count', 0) > 0:
            print("\n📢 Announcements 테이블 분석:")
            announcements_data = table_stats['announcements']['data']
            if announcements_data:
                sample = announcements_data[0]
                print(f"   컬럼: {list(sample.keys())}")
                print(f"   샘플 데이터: {json.dumps(sample, ensure_ascii=False, indent=2)}")
        
        # Recommendations 테이블 분석
        if table_stats.get('recommendations', {}).get('count', 0) > 0:
            print("\n🎯 Recommendations 테이블 분석:")
            recommendations_data = table_stats['recommendations']['data']
            if recommendations_data:
                sample = recommendations_data[0]
                print(f"   컬럼: {list(sample.keys())}")
                print(f"   샘플 데이터: {json.dumps(sample, ensure_ascii=False, indent=2)}")
        
        # Alpha Companies 테이블 분석 (기존 고객사)
        if table_stats.get('alpha_companies', {}).get('count', 0) > 0:
            print("\n🏢 Alpha Companies 테이블 분석 (기존 고객사):")
            alpha_data = table_stats['alpha_companies']['data']
            if alpha_data:
                sample = alpha_data[0]
                print(f"   컬럼: {list(sample.keys())}")
                print(f"   샘플 데이터: {json.dumps(sample, ensure_ascii=False, indent=2)}")
        
        # Recommendations2 테이블 분석
        if table_stats.get('recommendations2', {}).get('count', 0) > 0:
            print("\n📊 Recommendations2 테이블 분석:")
            rec2_data = table_stats['recommendations2']['data']
            if rec2_data:
                sample = rec2_data[0]
                print(f"   컬럼: {list(sample.keys())}")
                print(f"   샘플 데이터: {json.dumps(sample, ensure_ascii=False, indent=2)}")
        
        # Recommendations3 Active 테이블 분석
        if table_stats.get('recommendations3_active', {}).get('count', 0) > 0:
            print("\n🟢 Recommendations3 Active 테이블 분석:")
            rec3_data = table_stats['recommendations3_active']['data']
            if rec3_data:
                sample = rec3_data[0]
                print(f"   컬럼: {list(sample.keys())}")
                print(f"   샘플 데이터: {json.dumps(sample, ensure_ascii=False, indent=2)}")
        
        # 3. 데이터 연동 상태 분석
        print("\n🔗 데이터 연동 상태 분석")
        print("-" * 40)
        
        # Companies와 Alpha Companies 연동
        if table_stats.get('companies', {}).get('count', 0) > 0 and table_stats.get('alpha_companies', {}).get('count', 0) > 0:
            print("✅ Companies ↔ Alpha Companies: 양쪽 모두 데이터 존재")
        else:
            print("⚠️  Companies ↔ Alpha Companies: 일부 테이블에만 데이터 존재")
        
        # Recommendations와 Companies 연동
        if table_stats.get('recommendations', {}).get('count', 0) > 0 and table_stats.get('companies', {}).get('count', 0) > 0:
            print("✅ Recommendations ↔ Companies: 양쪽 모두 데이터 존재")
        else:
            print("⚠️  Recommendations ↔ Companies: 일부 테이블에만 데이터 존재")
        
        # Recommendations와 Announcements 연동
        if table_stats.get('recommendations', {}).get('count', 0) > 0 and table_stats.get('announcements', {}).get('count', 0) > 0:
            print("✅ Recommendations ↔ Announcements: 양쪽 모두 데이터 존재")
        else:
            print("⚠️  Recommendations ↔ Announcements: 일부 테이블에만 데이터 존재")
        
        # 4. 데이터 품질 분석
        print("\n📈 데이터 품질 분석")
        print("-" * 40)
        
        # 공고 데이터 품질
        if table_stats.get('announcements', {}).get('count', 0) > 0:
            announcements_result = supabase.table('announcements').select('*').execute()
            announcements_df = pd.DataFrame(announcements_result.data)
            
            print(f"📢 공고 데이터 품질:")
            print(f"   총 공고 수: {len(announcements_df)}")
            print(f"   마감일 있는 공고: {announcements_df['due_date'].notna().sum()}")
            print(f"   금액 정보 있는 공고: {announcements_df['amount_text'].notna().sum()}")
            print(f"   URL 있는 공고: {announcements_df['url'].notna().sum()}")
        
        # 추천 데이터 품질
        if table_stats.get('recommendations', {}).get('count', 0) > 0:
            recommendations_result = supabase.table('recommendations').select('*').execute()
            recommendations_df = pd.DataFrame(recommendations_result.data)
            
            print(f"\n🎯 추천 데이터 품질:")
            print(f"   총 추천 수: {len(recommendations_df)}")
            print(f"   점수 있는 추천: {recommendations_df['score'].notna().sum()}")
            print(f"   사유 있는 추천: {recommendations_df['reason'].notna().sum()}")
            if 'score' in recommendations_df.columns:
                print(f"   평균 점수: {recommendations_df['score'].mean():.2f}")
                print(f"   최고 점수: {recommendations_df['score'].max():.2f}")
                print(f"   최저 점수: {recommendations_df['score'].min():.2f}")
        
        # 5. 시스템 상태 요약
        print("\n📋 시스템 상태 요약")
        print("-" * 40)
        
        total_records = sum(stats['count'] for stats in table_stats.values())
        active_tables = sum(1 for stats in table_stats.values() if stats['count'] > 0)
        
        print(f"📊 총 레코드 수: {total_records:,}")
        print(f"📋 활성 테이블 수: {active_tables}/{len(tables)}")
        print(f"🔗 데이터베이스 연결: ✅ 정상")
        print(f"⏰ 분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return table_stats
        
    except Exception as e:
        print(f"❌ 데이터 분석 실패: {e}")
        return None

def analyze_data_relationships():
    """데이터 관계 분석"""
    print("\n🔗 데이터 관계 분석")
    print("=" * 60)
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 1. 회사-추천 관계 분석
        print("\n🏢 회사-추천 관계 분석:")
        
        # Alpha Companies와 Recommendations2 관계
        alpha_companies = supabase.table('alpha_companies').select('*').execute()
        recommendations2 = supabase.table('recommendations2').select('*').execute()
        
        if alpha_companies.data and recommendations2.data:
            alpha_df = pd.DataFrame(alpha_companies.data)
            rec2_df = pd.DataFrame(recommendations2.data)
            
            print(f"   Alpha Companies: {len(alpha_df)}개")
            print(f"   Recommendations2: {len(rec2_df)}개")
            
            # 회사별 추천 수 분석
            if '기업명' in rec2_df.columns:
                company_rec_counts = rec2_df['기업명'].value_counts()
                print(f"   회사별 평균 추천 수: {company_rec_counts.mean():.1f}")
                print(f"   최다 추천 회사: {company_rec_counts.index[0]} ({company_rec_counts.iloc[0]}개)")
        
        # 2. 공고-추천 관계 분석
        print("\n📢 공고-추천 관계 분석:")
        
        announcements = supabase.table('announcements').select('*').execute()
        recommendations = supabase.table('recommendations').select('*').execute()
        
        if announcements.data and recommendations.data:
            ann_df = pd.DataFrame(announcements.data)
            rec_df = pd.DataFrame(recommendations.data)
            
            print(f"   Announcements: {len(ann_df)}개")
            print(f"   Recommendations: {len(rec_df)}개")
            
            # 공고별 추천 수 분석
            if 'announcement_id' in rec_df.columns:
                ann_rec_counts = rec_df['announcement_id'].value_counts()
                print(f"   공고별 평균 추천 수: {ann_rec_counts.mean():.1f}")
                print(f"   최다 추천 공고: {ann_rec_counts.index[0]} ({ann_rec_counts.iloc[0]}개)")
        
        # 3. 데이터 일관성 검사
        print("\n🔍 데이터 일관성 검사:")
        
        # 중복 데이터 검사
        if recommendations2.data:
            rec2_df = pd.DataFrame(recommendations2.data)
            if '기업명' in rec2_df.columns and '공고이름' in rec2_df.columns:
                duplicates = rec2_df.duplicated(subset=['기업명', '공고이름']).sum()
                print(f"   중복 추천 데이터: {duplicates}개")
        
        # 빈 값 검사
        if recommendations2.data:
            rec2_df = pd.DataFrame(recommendations2.data)
            empty_fields = {}
            for col in rec2_df.columns:
                empty_count = rec2_df[col].isna().sum()
                if empty_count > 0:
                    empty_fields[col] = empty_count
            print(f"   빈 값이 있는 필드: {empty_fields}")
        
    except Exception as e:
        print(f"❌ 데이터 관계 분석 실패: {e}")

if __name__ == "__main__":
    print("🔍 Supabase 데이터 분석 도구")
    print("=" * 60)
    
    # 기본 데이터 분석
    table_stats = analyze_database()
    
    # 데이터 관계 분석
    analyze_data_relationships()
    
    print("\n✅ 분석 완료!")

