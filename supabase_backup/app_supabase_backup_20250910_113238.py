import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import altair as alt
from supabase import create_client, Client
import json
from config import SUPABASE_URL, SUPABASE_KEY

# Supabase 설정
@st.cache_resource
def init_supabase():
    """Supabase 클라이언트 초기화"""
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Supabase 연결 실패: {e}")
        st.stop()

supabase: Client = init_supabase()

@st.cache_data(ttl=60)
def load_companies() -> pd.DataFrame:
    """회사 데이터 로드 (alpha_companies 테이블 사용)"""
    try:
        result = supabase.table('alpha_companies').select('*').execute()
        df = pd.DataFrame(result.data)
        
        # 컬럼명을 기존 companies 테이블과 호환되도록 매핑
        if not df.empty:
            # 기본 컬럼 매핑
            df = df.rename(columns={
                'No.': 'id',
                '사업아이템 한 줄 소개': 'name',
                '기업형태': 'business_type',
                '소재지': 'region',
                '주업종 (사업자등록증 상)': 'industry',
                '특화분야': 'keywords'
            })
            
            # 추가 컬럼들을 별도로 추가
            df['설립일'] = df.get('설립연월일', '')
            df['매출'] = df.get('#매출', '')
            df['고용'] = df.get('#고용', '')
            df['특허'] = df.get('#기술특허(등록)', '')
            df['인증'] = df.get('#기업인증', '')
            df['주요산업'] = df.get('주요 산업', '')
            
            # years 컬럼 추가 (기본값)
            df['years'] = 0
                
            # stage 컬럼 추가 (기본값)
            df['stage'] = '예비'
            
            # preferred_uses, preferred_budget 컬럼 추가 (기본값)
            df['preferred_uses'] = ''
            df['preferred_budget'] = '소액'
        
        return df
    except Exception as e:
        st.error(f"회사 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_announcements() -> pd.DataFrame:
    """공고 데이터 로드"""
    try:
        result = supabase.table('announcements').select('*').execute()
        return pd.DataFrame(result.data)
    except Exception as e:
        st.error(f"공고 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_recommendations(company_id: int = None) -> pd.DataFrame:
    """추천 데이터 로드"""
    try:
        query = supabase.table('recommendations').select('*')
        if company_id:
            # alpha_companies의 No.와 recommendations의 company_id 매칭
            # alpha_companies에서 해당 ID가 있는지 확인
            company_result = supabase.table('alpha_companies').select('"No."').eq('"No."', company_id).execute()
            if company_result.data:
                query = query.eq('company_id', company_id)
            else:
                # alpha_companies에 없는 경우 빈 결과 반환
                return pd.DataFrame()
        result = query.execute()
        return pd.DataFrame(result.data)
    except Exception as e:
        st.error(f"추천 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_recommendations2(company_id: int = None) -> pd.DataFrame:
    """추천 데이터 로드 (recommendations2 테이블)"""
    try:
        query = supabase.table('recommendations2').select('*')
        if company_id:
            # alpha_companies 테이블의 ID와 recommendations2의 기업번호 매칭
            # 먼저 회사명으로 매칭 시도
            company_result = supabase.table('alpha_companies').select('"사업아이템 한 줄 소개"').eq('"No."', company_id).execute()
            if company_result.data:
                company_name = company_result.data[0]['사업아이템 한 줄 소개']
                # 회사명으로 recommendations2에서 검색
                query = supabase.table('recommendations2').select('*').ilike('기업명', f'%{company_name}%')
        result = query.execute()
        return pd.DataFrame(result.data)
    except Exception as e:
        st.error(f"추천 데이터 로드 실패 (recommendations2): {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_recommendations3_active(company_id: int = None) -> pd.DataFrame:
    """활성 추천 데이터 로드 (recommendations3_active 테이블)"""
    try:
        query = supabase.table('recommendations3_active').select('*')
        if company_id:
            # alpha_companies 테이블의 ID와 recommendations3_active의 기업번호 매칭
            # 먼저 회사명으로 매칭 시도
            company_result = supabase.table('alpha_companies').select('"사업아이템 한 줄 소개"').eq('"No."', company_id).execute()
            if company_result.data:
                company_name = company_result.data[0]['사업아이템 한 줄 소개']
                # 회사명으로 recommendations3_active에서 검색
                query = supabase.table('recommendations3_active').select('*').ilike('기업명', f'%{company_name}%')
        result = query.execute()
        return pd.DataFrame(result.data)
    except Exception as e:
        st.error(f"활성 추천 데이터 로드 실패 (recommendations3_active): {e}")
        return pd.DataFrame()

def save_company(company_data: Dict) -> bool:
    """회사 저장"""
    try:
        result = supabase.table('companies').insert(company_data).execute()
        return True
    except Exception as e:
        st.error(f"회사 저장 실패: {e}")
        return False

def delete_company(company_id: int) -> bool:
    """회사 삭제"""
    try:
        supabase.table('companies').delete().eq('id', company_id).execute()
        return True
    except Exception as e:
        st.error(f"회사 삭제 실패: {e}")
        return False

def load_notifications(company_id: int) -> List[str]:
    """알림 상태 로드"""
    try:
        # alpha_companies의 No.와 notification_states의 company_id 매칭
        result = supabase.table('notification_states').select('last_seen_announcement_ids').eq('company_id', company_id).execute()
        if result.data:
            return result.data[0]['last_seen_announcement_ids'] or []
        return []
    except Exception as e:
        st.error(f"알림 상태 로드 실패: {e}")
        return []

def save_notifications(company_id: int, announcement_ids: List[str]) -> bool:
    """알림 상태 저장"""
    try:
        # 기존 레코드 확인
        existing = supabase.table('notification_states').select('id').eq('company_id', company_id).execute()
        
        data = {
            'company_id': company_id,
            'last_seen_announcement_ids': announcement_ids,
            'last_updated': datetime.now().isoformat()
        }
        
        if existing.data:
            # 업데이트
            supabase.table('notification_states').update(data).eq('company_id', company_id).execute()
        else:
            # 삽입
            supabase.table('notification_states').insert(data).execute()
        
        return True
    except Exception as e:
        st.error(f"알림 상태 저장 실패: {e}")
        return False

def calculate_dday(due_date: str) -> Optional[int]:
    """D-Day 계산"""
    if pd.isna(due_date) or due_date == '':
        return None
    
    try:
        due = datetime.strptime(due_date, '%Y-%m-%d').date()
        today = date.today()
        return (due - today).days
    except:
        return None

def format_recommendation_reason(reason: str, score: float) -> str:
    """추천 사유 포맷팅"""
    if pd.isna(reason) or reason == '' or reason is None or str(reason).strip() == '':
        # 기본 추천 사유 생성
        if score >= 80:
            return "높은 적합도 - 키워드 매칭 및 조건 충족"
        elif score >= 60:
            return "적합도 양호 - 주요 조건 충족"
        elif score >= 40:
            return "보통 적합도 - 일부 조건 충족"
        else:
            return "낮은 적합도 - 참고용"
    return str(reason).strip()

def render_sidebar():
    """사이드바 렌더링"""
    st.sidebar.title("🏢 회사 관리")
    
    # 기존 고객사 목록 (alpha_companies 테이블 사용)
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
        
        # 회사 선택 (사업아이템으로 표시)
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
    
    st.sidebar.divider()
    
    # 신규 회사 추가 폼
    st.sidebar.subheader("신규 회사 추가")
    
    with st.sidebar.form("new_company_form"):
        name = st.text_input("회사명", key="new_name")
        business_type = st.selectbox("사업자 유형", ["법인", "개인"], key="new_business_type")
        region = st.text_input("지역", key="new_region")
        years = st.number_input("업력", min_value=0, max_value=100, value=0, key="new_years")
        stage = st.selectbox("성장단계", ["예비", "초기", "성장"], key="new_stage")
        industry = st.text_input("업종", key="new_industry")
        keywords = st.text_input("키워드 (쉼표로 구분)", key="new_keywords")
        preferred_uses = st.text_input("선호 지원용도 (쉼표로 구분)", key="new_preferred_uses")
        preferred_budget = st.selectbox("선호 예산규모", ["소액", "중간", "대형"], key="new_preferred_budget")
        
        if st.form_submit_button("신규 회사 추가"):
            if name:
                company_data = {
                    'name': name,
                    'business_type': business_type,
                    'region': region,
                    'years': years,
                    'stage': stage,
                    'industry': industry,
                    'keywords': keywords.split(',') if keywords else [],
                    'preferred_uses': preferred_uses.split(',') if preferred_uses else [],
                    'preferred_budget': preferred_budget
                }
                
                if save_company(company_data):
                    st.success("회사가 추가되었습니다!")
                    st.rerun()
            else:
                st.error("회사명을 입력해주세요.")

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
            # 공고 정보와 조인
            announcements_df = load_announcements()
            merged_df = recommendations_df.merge(
                announcements_df, 
                left_on='announcement_id', 
                right_on='id', 
                how='inner',
                suffixes=('', '_ann')
            )
            
            if not merged_df.empty:
                # 컬럼 선택 및 정렬 (링크와 추천 사유 포함)
                display_columns = ['rank', 'score', 'title', 'agency', 'amount_text', 'due_date', 'update_type', 'url', 'reason']
                available_columns = [col for col in display_columns if col in merged_df.columns]
                
                # Arrow 직렬화 문제 방지를 위해 데이터 타입 정리
                display_df = merged_df[available_columns].copy()
                
                # 추천 사유 포맷팅
                if 'reason' in display_df.columns and 'score' in display_df.columns:
                    display_df['reason'] = display_df.apply(
                        lambda row: format_recommendation_reason(row['reason'], row['score']), 
                        axis=1
                    )
                
                for col in display_df.columns:
                    if display_df[col].dtype == 'object':
                        display_df[col] = display_df[col].astype(str)
                
                st.dataframe(
                    display_df,
                    width='stretch',
                    column_config={
                        "url": st.column_config.LinkColumn("링크", display_text="공고 보기"),
                        "reason": st.column_config.TextColumn("추천 이유", width="large"),
                        "title": st.column_config.TextColumn("공고명", width="large"),
                        "agency": st.column_config.TextColumn("주관기관", width="medium"),
                        "amount_text": st.column_config.TextColumn("투자금액", width="medium"),
                        "due_date": st.column_config.DateColumn("마감일", width="small"),
                        "update_type": st.column_config.TextColumn("상태", width="small"),
                        "score": st.column_config.NumberColumn("점수", format="%.1f", width="small"),
                        "rank": st.column_config.NumberColumn("순위", width="small")
                    }
                )
            else:
                st.info("해당 회사의 추천 결과가 없습니다.")
        else:
            st.info("추천 데이터가 없습니다.")
    
    with tab2:
        # 활성 공고만 필터링 (마감되지 않은 공고)
        recommendations_df = load_recommendations(company['id'])
        if not recommendations_df.empty:
            # 오늘 날짜 기준으로 활성 공고 필터링
            today = date.today()
            active_recommendations = recommendations_df[
                (recommendations_df['end_date'] >= today.strftime('%Y-%m-%d')) |
                (recommendations_df['end_date'].isna())
            ]
            
            if not active_recommendations.empty:
                # 공고 정보와 조인
                announcements_df = load_announcements()
                merged_df = active_recommendations.merge(
                    announcements_df, 
                    left_on='announcement_id', 
                    right_on='id', 
                    how='inner',
                    suffixes=('', '_ann')
                )
                
                display_columns = ['rank', 'score', 'title', 'agency', 'amount_text', 'due_date', 'update_type', 'url', 'reason']
                available_columns = [col for col in display_columns if col in merged_df.columns]
                
                # Arrow 직렬화 문제 방지를 위해 데이터 타입 정리
                display_df = merged_df[available_columns].copy()
                
                # 추천 사유 포맷팅
                if 'reason' in display_df.columns and 'score' in display_df.columns:
                    display_df['reason'] = display_df.apply(
                        lambda row: format_recommendation_reason(row['reason'], row['score']), 
                        axis=1
                    )
                
                for col in display_df.columns:
                    if display_df[col].dtype == 'object':
                        display_df[col] = display_df[col].astype(str)
                
                st.dataframe(
                    display_df,
                    width='stretch',
                    column_config={
                        "url": st.column_config.LinkColumn("링크", display_text="공고 보기"),
                        "reason": st.column_config.TextColumn("추천 이유", width="large"),
                        "title": st.column_config.TextColumn("공고명", width="large"),
                        "agency": st.column_config.TextColumn("주관기관", width="medium"),
                        "amount_text": st.column_config.TextColumn("투자금액", width="medium"),
                        "due_date": st.column_config.DateColumn("마감일", width="small"),
                        "update_type": st.column_config.TextColumn("상태", width="small"),
                        "score": st.column_config.NumberColumn("점수", format="%.1f", width="small"),
                        "rank": st.column_config.NumberColumn("순위", width="small")
                    }
                )
            else:
                st.info("활성 추천 결과가 없습니다.")
        else:
            st.info("활성 추천 데이터가 없습니다.")

def render_alerts_tab():
    """신규 공고 알림 탭 렌더링 (recommendations2 테이블 사용)"""
    if 'selected_company' not in st.session_state:
        st.info("사이드바에서 회사를 선택해주세요.")
        return
    
    company = st.session_state['selected_company']
    st.subheader(f"🔔 {company['name']} 신규 공고 알림")
    
    # 알림 상태 로드
    last_seen_ids = load_notifications(company['id'])
    
    # 활성 추천 데이터 로드 (recommendations2 테이블 사용)
    recommendations2_df = load_recommendations2(company['id'])
    
    if not recommendations2_df.empty:
        # 활성 공고만 필터링 (마감일 기준)
        today = date.today()
        active_recommendations = recommendations2_df[
            (recommendations2_df['마감일'] >= today.strftime('%Y-%m-%d')) |
            (recommendations2_df['마감일'].isna())
        ]
        
        if not active_recommendations.empty:
            # 신규 공고 필터링 (공고이름 기준으로 비교)
            # recommendations2에서는 공고 ID가 없으므로 공고이름으로 비교
            last_seen_names = []
            if last_seen_ids:
                # 기존 알림 상태에서 공고 이름들을 가져와야 함
                # 이 부분은 간단히 모든 공고를 신규로 표시하도록 수정
                pass
            
            # 일단 모든 활성 공고를 신규로 표시 (실제 구현에서는 더 정교한 로직 필요)
            new_announcements = active_recommendations
            
            if not new_announcements.empty:
                st.success(f"🆕 {len(new_announcements)}개의 활성 공고가 있습니다!")
                
                # recommendations2 테이블의 컬럼을 직접 사용
                display_columns = ['추천순위', '추천점수', '공고이름', '추천이유', '모집일', '마감일', '투자금액', '공고상태']
                available_columns = [col for col in display_columns if col in new_announcements.columns]
                
                # 데이터 타입 정리
                display_df = new_announcements[available_columns].copy()
                for col in display_df.columns:
                    if display_df[col].dtype == 'object':
                        display_df[col] = display_df[col].astype(str)
                
                st.dataframe(
                    display_df,
                    width='stretch',
                    column_config={
                        "추천이유": st.column_config.TextColumn("추천 이유", width="large"),
                        "공고이름": st.column_config.TextColumn("공고명", width="large"),
                        "투자금액": st.column_config.TextColumn("투자금액", width="medium"),
                        "마감일": st.column_config.DateColumn("마감일", width="small"),
                        "공고상태": st.column_config.TextColumn("상태", width="small"),
                        "추천점수": st.column_config.NumberColumn("점수", format="%.0f", width="small"),
                        "추천순위": st.column_config.NumberColumn("순위", width="small")
                    }
                )
                
                # 모두 확인 처리 버튼
                if st.button("모두 확인 처리", type="primary"):
                    # 현재 활성 추천들의 공고이름을 스냅샷에 저장
                    current_names = active_recommendations['공고이름'].tolist()
                    
                    if save_notifications(company['id'], current_names):
                        st.success("모든 공고를 확인 처리했습니다!")
                        st.rerun()
            else:
                st.info("신규 공고가 없습니다.")
        else:
            st.info("해당 회사의 활성 추천이 없습니다.")
    else:
        st.info("활성 추천 데이터가 없습니다.")

def render_roadmap_tab():
    """12개월 로드맵 탭 렌더링 (recommendations2 테이블 사용)"""
    if 'selected_company' not in st.session_state:
        st.info("사이드바에서 회사를 선택해주세요.")
        return
    
    company = st.session_state['selected_company']
    st.subheader(f"🗓️ {company['name']} 12개월 로드맵")
    
    # 추천 데이터 로드 (recommendations2 테이블 사용)
    recommendations2_df = load_recommendations2(company['id'])
    
    if not recommendations2_df.empty:
        # 월별 데이터 준비
        monthly_data = []
        monthly_matches = {}  # DataFrame을 별도로 저장
        
        for month in range(1, 13):
            month_matches = recommendations2_df[
                recommendations2_df['공고월'] == month
            ]
            
            # recommendations2에서는 투자금액이 텍스트이므로 숫자 추출 시도
            total_amount = 0
            if '투자금액' in month_matches.columns:
                for amount_text in month_matches['투자금액']:
                    if pd.notna(amount_text) and isinstance(amount_text, str):
                        # "최대 1억원" 형태에서 숫자 추출
                        import re
                        numbers = re.findall(r'[\d,]+', amount_text.replace('억', '00000000').replace('천만', '0000000').replace('만', '0000'))
                        if numbers:
                            try:
                                total_amount += int(numbers[0].replace(',', ''))
                            except:
                                pass
            
            monthly_data.append({
                'Month': f"{month}월",
                'Count': len(month_matches),
                'TotalAmount': total_amount
            })
            
            # DataFrame을 별도 딕셔너리에 저장
            monthly_matches[month] = month_matches
        
        # 월별 금액 합계 차트
        chart_data = pd.DataFrame(monthly_data)
        if not chart_data.empty:
            chart = alt.Chart(chart_data).mark_bar().encode(
                x='Month:O',
                y='TotalAmount:Q',
                tooltip=['Month', 'TotalAmount']
            ).properties(
                title="월별 예상 지원금액",
                width=600,
                height=300
            )
            st.altair_chart(chart)
        
        # 월별 상세 정보
        for month_data in monthly_data:
            month_num = int(month_data['Month'].replace('월', ''))
            month_matches_df = monthly_matches.get(month_num, pd.DataFrame())
            
            with st.expander(f"{month_data['Month']} ({month_data['Count']}개 공고, {month_data['TotalAmount']:,}원)"):
                if not month_matches_df.empty:
                    # recommendations2 테이블의 컬럼을 직접 사용
                    display_columns = ['추천순위', '추천점수', '공고이름', '추천이유', '모집일', '마감일', '투자금액', '공고상태']
                    available_columns = [col for col in display_columns if col in month_matches_df.columns]
                    
                    # 데이터 타입 정리
                    display_df = month_matches_df[available_columns].copy()
                    for col in display_df.columns:
                        if display_df[col].dtype == 'object':
                            display_df[col] = display_df[col].astype(str)
                    
                    st.dataframe(
                        display_df,
                        width='stretch',
                        column_config={
                            "추천이유": st.column_config.TextColumn("추천 이유", width="large"),
                            "공고이름": st.column_config.TextColumn("공고명", width="large"),
                            "투자금액": st.column_config.TextColumn("투자금액", width="medium"),
                            "마감일": st.column_config.DateColumn("마감일", width="small"),
                            "공고상태": st.column_config.TextColumn("상태", width="small"),
                            "추천점수": st.column_config.NumberColumn("점수", format="%.0f", width="small"),
                            "추천순위": st.column_config.NumberColumn("순위", width="small")
                        }
                    )
                else:
                    st.info("이 달에는 추천 공고가 없습니다. 탐색/서류준비/인증취득 등의 활동을 고려해보세요.")
        
        # CSV 다운로드
        csv = recommendations2_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="로드맵 데이터 다운로드 (CSV)",
            data=csv,
            file_name=f"{company['name']}_roadmap_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("추천 데이터가 없습니다.")

def render_recommendations2_tab():
    """추천 데이터 탭 렌더링 (recommendations2 테이블)"""
    if 'selected_company' not in st.session_state:
        st.info("사이드바에서 회사를 선택해주세요.")
        return
    
    company = st.session_state['selected_company']
    st.subheader(f"📊 {company['name']} 추천 데이터 (한글 버전)")
    
    # 탭 선택
    tab1, tab2 = st.tabs(["전체 추천", "활성 공고만"])
    
    with tab1:
        # 전체 추천 (recommendations2 + recommendations3_active, 중복 제거)
        recommendations2_df = load_recommendations2(company['id'])
        active_recommendations_df = load_recommendations3_active(company['id'])
        
        # 두 데이터프레임을 합치되 중복 제거
        combined_df = pd.DataFrame()
        
        if not recommendations2_df.empty:
            # recommendations2 데이터에 소스 표시
            recommendations2_df = recommendations2_df.copy()
            recommendations2_df['데이터소스'] = '전체'
            combined_df = pd.concat([combined_df, recommendations2_df], ignore_index=True)
        
        if not active_recommendations_df.empty:
            # recommendations3_active 데이터에 소스 표시
            active_recommendations_df = active_recommendations_df.copy()
            active_recommendations_df['데이터소스'] = '활성'
            
            # 중복 제거: 공고이름 기준으로 중복 확인
            if not combined_df.empty:
                # 기존 데이터에 없는 활성 공고만 추가
                existing_announcements = set(combined_df['공고이름'].tolist())
                new_active = active_recommendations_df[
                    ~active_recommendations_df['공고이름'].isin(existing_announcements)
                ]
                combined_df = pd.concat([combined_df, new_active], ignore_index=True)
            else:
                combined_df = active_recommendations_df
        
        if not combined_df.empty:
            st.info(f"📊 총 {len(combined_df)}개의 추천 공고 (전체 + 활성, 중복 제거)")
            
            # 컬럼명을 한글로 매핑
            display_columns = ['추천순위', '추천점수', '공고이름', '추천이유', '모집일', '마감일', '투자금액', '공고상태', '데이터소스']
            available_columns = [col for col in display_columns if col in combined_df.columns]
            
            # 데이터 타입 정리
            display_df = combined_df[available_columns].copy()
            for col in display_df.columns:
                if display_df[col].dtype == 'object':
                    display_df[col] = display_df[col].astype(str)
            
            # 추천순위로 정렬
            if '추천순위' in display_df.columns:
                display_df = display_df.sort_values('추천순위')
            
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "추천이유": st.column_config.TextColumn("추천 이유", width="large"),
                    "공고이름": st.column_config.TextColumn("공고명", width="large"),
                    "투자금액": st.column_config.TextColumn("투자금액", width="medium"),
                    "마감일": st.column_config.DateColumn("마감일", width="small"),
                    "공고상태": st.column_config.TextColumn("상태", width="small"),
                    "데이터소스": st.column_config.TextColumn("소스", width="small"),
                    "추천점수": st.column_config.NumberColumn("점수", format="%.0f", width="small"),
                    "추천순위": st.column_config.NumberColumn("순위", width="small")
                }
            )
        else:
            st.info("해당 회사의 추천 결과가 없습니다.")
    
    with tab2:
        # 활성 공고만 (recommendations3_active 테이블 사용)
        active_recommendations_df = load_recommendations3_active(company['id'])
        if not active_recommendations_df.empty:
            st.success(f"🟢 {len(active_recommendations_df)}개의 활성 공고가 있습니다!")
            
            display_columns = ['추천순위', '추천점수', '공고이름', '추천이유', '모집일', '마감일', '투자금액', '공고상태', '남은기간/마감여부']
            available_columns = [col for col in display_columns if col in active_recommendations_df.columns]
            
            # 데이터 타입 정리
            display_df = active_recommendations_df[available_columns].copy()
            for col in display_df.columns:
                if display_df[col].dtype == 'object':
                    display_df[col] = display_df[col].astype(str)
            
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "추천이유": st.column_config.TextColumn("추천 이유", width="large"),
                    "공고이름": st.column_config.TextColumn("공고명", width="large"),
                    "투자금액": st.column_config.TextColumn("투자금액", width="medium"),
                    "마감일": st.column_config.DateColumn("마감일", width="small"),
                    "공고상태": st.column_config.TextColumn("상태", width="small"),
                    "남은기간/마감여부": st.column_config.TextColumn("남은기간", width="small"),
                    "추천점수": st.column_config.NumberColumn("점수", format="%.0f", width="small"),
                    "추천순위": st.column_config.NumberColumn("순위", width="small")
                }
            )
        else:
            st.info("활성 추천 데이터가 없습니다.")

def main():
    """메인 함수"""
    st.set_page_config(
        page_title="Advisor MVP - Supabase",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏛️ 정부지원사업 맞춤 추천 시스템 (Supabase)")
    st.markdown("---")
    
    # 사이드바 렌더링
    render_sidebar()
    
    # 메인 컨텐츠
    if 'selected_company' in st.session_state:
        company = st.session_state['selected_company']
        
        # 선택된 회사 헤더 (alpha_companies 정보 활용)
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.subheader(f"🏢 {company['name']}")
        with col2:
            st.metric("성장단계", company.get('stage', 'N/A'))
        with col3:
            st.metric("업력", f"{company.get('years', 0)}년")
        with col4:
            # alpha_companies의 추가 정보 표시
            if '매출' in company:
                st.metric("매출", company.get('매출', 'N/A'))
            else:
                st.metric("업종", company.get('industry', 'N/A'))
        
        # 탭 구성
        tab1, tab2, tab3, tab4 = st.tabs(["📊 추천 데이터 (한글)", "🔔 신규 공고 알림", "🗓️ 12개월 로드맵", "📋 맞춤 추천"])
        
        with tab1:
            render_recommendations2_tab()
        
        with tab2:
            render_alerts_tab()
        
        with tab3:
            render_roadmap_tab()
        
        with tab4:
            render_recommendations_tab()
    else:
        st.info("👈 사이드바에서 회사를 선택해주세요.")

if __name__ == "__main__":
    main()
