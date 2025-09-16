import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import altair as alt

# 데모용 데이터 (Supabase 없이 작동)
DEMO_COMPANIES = [
    {
        'id': 1,
        'name': '전문 기획팀이 부재로 기획 및 스토리텔링 역량이 부족한 중소규모 건축기획사를 위한 기획 솔루션 "아키스토리 AI"',
        'business_type': '법인',
        'region': '서울',
        'years': 3,
        'stage': '초기',
        'industry': '건축/부동산',
        'keywords': ['AI', '건축', '기획', '스토리텔링'],
        'preferred_uses': ['R&D', '마케팅'],
        'preferred_budget': '중간'
    },
    {
        'id': 2,
        'name': '통합 API 운영을 통한 스마트 가로등',
        'business_type': '법인',
        'region': '경기',
        'years': 5,
        'stage': '성장',
        'industry': 'IoT/스마트시티',
        'keywords': ['IoT', 'API', '스마트시티', '가로등'],
        'preferred_uses': ['R&D', '인프라'],
        'preferred_budget': '대형'
    },
    {
        'id': 3,
        'name': 'AI 기반 개인맞춤 헬스케어 플랫폼',
        'business_type': '법인',
        'region': '서울',
        'years': 2,
        'stage': '초기',
        'industry': '헬스케어',
        'keywords': ['AI', '헬스케어', '개인맞춤', '플랫폼'],
        'preferred_uses': ['R&D', '마케팅'],
        'preferred_budget': '소액'
    }
]

DEMO_RECOMMENDATIONS = [
    {
        'company_id': 1,
        'rank': 1,
        'score': 95,
        'title': '2025년 AI 기반 건축 설계 지원사업',
        'agency': '국토교통부',
        'amount_text': '최대 5억원',
        'due_date': '2025-03-15',
        'status': '모집중',
        'reason': 'AI 기술과 건축 분야의 완벽한 매칭, 기획 역량 강화에 최적'
    },
    {
        'company_id': 1,
        'rank': 2,
        'score': 88,
        'title': '스마트 건축 기술개발 지원사업',
        'agency': '과학기술정보통신부',
        'amount_text': '최대 3억원',
        'due_date': '2025-04-30',
        'status': '모집중',
        'reason': '건축 기술혁신과 스토리텔링 요소가 강조된 사업'
    },
    {
        'company_id': 2,
        'rank': 1,
        'score': 92,
        'title': '스마트시티 통합 플랫폼 구축사업',
        'agency': '행정안전부',
        'amount_text': '최대 10억원',
        'due_date': '2025-02-28',
        'status': '모집중',
        'reason': 'IoT 기반 스마트시티 인프라 구축에 최적화된 사업'
    },
    {
        'company_id': 2,
        'rank': 2,
        'score': 85,
        'title': '공공데이터 활용 API 개발 지원사업',
        'agency': '과학기술정보통신부',
        'amount_text': '최대 2억원',
        'due_date': '2025-05-15',
        'status': '모집중',
        'reason': 'API 운영 경험과 공공데이터 활용 역량이 요구되는 사업'
    }
]

def load_companies():
    """데모 회사 데이터 로드"""
    return pd.DataFrame(DEMO_COMPANIES)

def load_recommendations(company_id: int = None):
    """데모 추천 데이터 로드"""
    df = pd.DataFrame(DEMO_RECOMMENDATIONS)
    if company_id:
        df = df[df['company_id'] == company_id]
    return df

def render_sidebar():
    """사이드바 렌더링"""
    st.sidebar.title("🏢 회사 관리")
    
    # 기존 고객사 목록
    st.sidebar.subheader("기존 고객사")
    companies_df = load_companies()
    
    if not companies_df.empty:
        # 검색 기능
        search_term = st.sidebar.text_input("🔍 회사 검색", key="existing_search")
        if search_term:
            filtered_companies = companies_df[
                companies_df['name'].str.contains(search_term, case=False, na=False)
            ]
        else:
            filtered_companies = companies_df
        
        # 회사 선택
        company_names = filtered_companies['name'].tolist()
        if company_names:
            selected_company = st.sidebar.selectbox(
                "회사 선택",
                company_names,
                key="existing_company_select"
            )
            if selected_company:
                selected_company_data = filtered_companies[filtered_companies['name'] == selected_company].iloc[0]
                st.session_state['selected_company'] = selected_company_data.to_dict()
        else:
            st.sidebar.info("검색 결과가 없습니다.")
    else:
        st.sidebar.info("기존 고객사 데이터가 없습니다.")

def render_recommendations_tab():
    """맞춤 추천 탭 렌더링"""
    if 'selected_company' not in st.session_state:
        st.info("사이드바에서 회사를 선택해주세요.")
        return
    
    company = st.session_state['selected_company']
    st.subheader(f"📋 {company['name']} 맞춤 추천")
    
    # 탭 선택
    tab1, tab2 = st.tabs(["전체 추천", "활성 공고만"])
    
    with tab1:
        recommendations_df = load_recommendations(company['id'])
        if not recommendations_df.empty:
            st.info(f"📊 총 {len(recommendations_df)}개의 추천 공고")
            
            # 데이터 표시
            display_columns = ['rank', 'score', 'title', 'agency', 'amount_text', 'due_date', 'status', 'reason']
            display_df = recommendations_df[display_columns].copy()
            
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "reason": st.column_config.TextColumn("추천 이유", width="large"),
                    "title": st.column_config.TextColumn("공고명", width="large"),
                    "amount_text": st.column_config.TextColumn("투자금액", width="medium"),
                    "due_date": st.column_config.DateColumn("마감일", width="small"),
                    "status": st.column_config.TextColumn("상태", width="small"),
                    "score": st.column_config.NumberColumn("점수", format="%.0f", width="small"),
                    "rank": st.column_config.NumberColumn("순위", width="small")
                }
            )
        else:
            st.info("해당 회사의 추천 결과가 없습니다.")
    
    with tab2:
        # 활성 공고만 (마감일이 미래인 것)
        active_recommendations = recommendations_df[recommendations_df['status'] == '모집중']
        if not active_recommendations.empty:
            st.success(f"🟢 {len(active_recommendations)}개의 활성 공고가 있습니다!")
            
            display_columns = ['rank', 'score', 'title', 'agency', 'amount_text', 'due_date', 'status', 'reason']
            display_df = active_recommendations[display_columns].copy()
            
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "reason": st.column_config.TextColumn("추천 이유", width="large"),
                    "title": st.column_config.TextColumn("공고명", width="large"),
                    "amount_text": st.column_config.TextColumn("투자금액", width="medium"),
                    "due_date": st.column_config.DateColumn("마감일", width="small"),
                    "status": st.column_config.TextColumn("상태", width="small"),
                    "score": st.column_config.NumberColumn("점수", format="%.0f", width="small"),
                    "rank": st.column_config.NumberColumn("순위", width="small")
                }
            )
        else:
            st.info("활성 추천 데이터가 없습니다.")

def main():
    """메인 함수"""
    st.set_page_config(
        page_title="Advisor MVP - Demo",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏛️ 정부지원사업 맞춤 추천 시스템 (Demo)")
    st.markdown("---")
    
    # 사이드바 렌더링
    render_sidebar()
    
    # 메인 컨텐츠
    if 'selected_company' in st.session_state:
        company = st.session_state['selected_company']
        
        # 선택된 회사 헤더
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            company_name = company.get('name', '회사명 없음')
            st.subheader(f"🏢 {company_name}")
        with col2:
            st.metric("성장단계", company.get('stage', 'N/A'))
        with col3:
            st.metric("업력", f"{company.get('years', 0)}년")
        with col4:
            st.metric("업종", company.get('industry', 'N/A'))
        
        # 회사 상세 정보 표시
        st.write("---")
        st.write("### 📋 회사 상세 정보")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**사업자 유형:** {company.get('business_type', 'N/A')}")
            st.write(f"**지역:** {company.get('region', 'N/A')}")
            st.write(f"**업종:** {company.get('industry', 'N/A')}")
        
        with col2:
            st.write(f"**키워드:** {', '.join(company.get('keywords', []))}")
            st.write(f"**선호 지원용도:** {', '.join(company.get('preferred_uses', []))}")
            st.write(f"**선호 예산규모:** {company.get('preferred_budget', 'N/A')}")
        
        st.write("---")
        
        # 탭 구성
        tab1 = st.tabs(["📊 맞춤 추천"])
        
        with tab1:
            render_recommendations_tab()
    else:
        st.info("👈 사이드바에서 회사를 선택해주세요.")

if __name__ == "__main__":
    main()

