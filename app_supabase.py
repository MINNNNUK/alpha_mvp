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
        # 환경변수에서 Supabase 설정 가져오기
        url = os.getenv("SUPABASE_URL", "https://demo.supabase.co")
        key = os.getenv("SUPABASE_KEY", "demo-key")
        
        if url == "https://demo.supabase.co" or key == "demo-key":
            st.warning("⚠️ 데모 모드로 실행 중입니다. 실제 데이터를 사용하려면 Supabase 설정이 필요합니다.")
            return None
        
        return create_client(url, key)
    except Exception as e:
        st.warning(f"Supabase 연결 실패: {e}")
        st.info("데모 모드로 실행합니다.")
        return None

supabase: Client = init_supabase()

def calculate_support_status(start_date, end_date, reference_date=None):
    """접수시작일과 접수마감일을 기준으로 지원 가능 여부를 판단합니다."""
    if reference_date is None:
        reference_date = datetime(2025, 9, 16)  # 기준일 설정
    
    try:
        # 날짜 파싱
        if pd.isna(start_date) or pd.isna(end_date):
            return "정보부족"
        
        # 문자열을 datetime으로 변환
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        
        # 기준일이 접수시작일보다 이른 경우
        if reference_date < start_date:
            return "접수예정"
        # 기준일이 접수마감일보다 늦은 경우
        elif reference_date > end_date:
            return "접수마감"
        # 기준일이 접수기간 내에 있는 경우
        else:
            return "지원가능"
            
    except Exception as e:
        return "정보부족"

@st.cache_data(ttl=30)  # 캐시 시간을 30초로 단축하여 새로 추가된 회사가 빠르게 반영되도록
def load_companies() -> pd.DataFrame:
    """회사 데이터 로드 (alpha_companies2 + companies 테이블 통합)"""
    try:
        if supabase is None:
            # 데모 데이터 반환
            return pd.DataFrame({
                'id': [1, 2, 3],
                'name': ['데모 회사 1', '데모 회사 2', '데모 회사 3'],
                'business_type': ['법인', '개인', '법인'],
                'region': ['서울', '경기', '부산'],
                'industry': ['IT', '제조업', '서비스업'],
                'keywords': [['AI', '빅데이터'], ['제조', '자동화'], ['서비스', '플랫폼']],
                'years': [5, 3, 7],
                'stage': ['성장', '초기', '성장'],
                'preferred_uses': [['R&D', '마케팅'], ['설비', '인력'], ['플랫폼', '마케팅']],
                'preferred_budget': ['중간', '소액', '대형']
            })
        
        all_companies = []
        
        # 1. alpha_companies2 테이블에서 기존 고객사 데이터 로드
        try:
            alpha_result = supabase.table('alpha_companies2').select('*').execute()
            alpha_df = pd.DataFrame(alpha_result.data)
            
            if not alpha_df.empty:
                # 컬럼명을 companies 테이블과 호환되도록 매핑
                alpha_df = alpha_df.rename(columns={
                    'No.': 'original_id',
                    '사업아이템 한 줄 소개': 'name',
                    '기업형태': 'business_type',
                    '소재지': 'region',
                    '주업종 (사업자등록증 상)': 'industry',
                    '특화분야': 'keywords'
                })
                
                # ID 충돌 방지를 위해 alpha_companies2는 음수 ID 사용
                alpha_df['id'] = -alpha_df['original_id']
                
                # 기업명 추출 (사업아이템 한 줄 소개에서 "기업명 - " 부분 추출)
                if 'name' in alpha_df.columns:
                    # 먼저 기존 기업명 컬럼이 있는지 확인
                    if '기업명' in alpha_df.columns:
                        alpha_df['company_name'] = alpha_df['기업명']
                    else:
                        # 기업명이 없으면 사업아이템에서 추출 시도
                        alpha_df['company_name'] = alpha_df['name'].str.extract(r'^([^-]+) - ')[0].str.strip()
                        # 기업명이 추출되지 않은 경우 전체 이름 사용
                        alpha_df['company_name'] = alpha_df['company_name'].fillna(alpha_df['name'])
                
                # 추가 컬럼들을 별도로 추가
                alpha_df['설립일'] = alpha_df.get('설립연월일', '')
                alpha_df['매출'] = alpha_df.get('#매출', '')
                alpha_df['고용'] = alpha_df.get('#고용', '')
                alpha_df['특허'] = alpha_df.get('#기술특허(등록)', '')
                alpha_df['인증'] = alpha_df.get('#기업인증', '')
                alpha_df['주요산업'] = alpha_df.get('주요 산업', '')
                
                # years 컬럼 추가 (기본값)
                alpha_df['years'] = 0
                    
                # stage 컬럼 추가 (기본값)
                alpha_df['stage'] = '예비'
                
                # preferred_uses, preferred_budget 컬럼 추가 (기본값)
                alpha_df['preferred_uses'] = ''
                alpha_df['preferred_budget'] = '소액'
                
                # 테이블 구분을 위한 컬럼 추가
                alpha_df['source_table'] = 'alpha_companies2'
                
                all_companies.append(alpha_df)
        except Exception as e:
            st.warning(f"alpha_companies2 테이블 로드 실패: {e}")
        
        # 2. companies 테이블에서 신규 회사 데이터 로드
        try:
            companies_result = supabase.table('companies').select('*').execute()
            companies_df = pd.DataFrame(companies_result.data)
            
            if not companies_df.empty:
                # company_name 컬럼 추가 (name과 동일)
                companies_df['company_name'] = companies_df['name']
                
                # 테이블 구분을 위한 컬럼 추가
                companies_df['source_table'] = 'companies'
                
                all_companies.append(companies_df)
        except Exception as e:
            st.warning(f"companies 테이블 로드 실패: {e}")
        
        # 3. 모든 회사 데이터 통합
        if all_companies:
            combined_df = pd.concat(all_companies, ignore_index=True)
            # 최신 추가된 회사가 먼저 보이도록 정렬 (ID 기준 내림차순)
            combined_df = combined_df.sort_values('id', ascending=False)
            return combined_df
        else:
            return pd.DataFrame()
        
    except Exception as e:
        st.error(f"회사 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_announcements() -> pd.DataFrame:
    """공고 데이터 로드 (biz2 + kstartup2 테이블 통합)"""
    try:
        if supabase is None:
            return pd.DataFrame()
        
        # biz2 테이블 데이터 로드
        biz_result = supabase.table('biz2').select('*').execute()
        biz_df = pd.DataFrame(biz_result.data)
        
        # kstartup2 테이블 데이터 로드
        kstartup_result = supabase.table('kstartup2').select('*').execute()
        kstartup_df = pd.DataFrame(kstartup_result.data)
        
        # biz2 데이터 정규화
        if not biz_df.empty:
            biz_df['source'] = 'Bizinfo'
            biz_df['id'] = biz_df['번호'].astype(str)
            biz_df['title'] = biz_df['공고명']
            biz_df['agency'] = biz_df['사업수행기관']
            biz_df['region'] = ''  # biz2에는 지역 정보가 없음
            biz_df['due_date'] = biz_df['신청종료일자']
            biz_df['info_session_date'] = biz_df['신청시작일자']
            biz_df['url'] = biz_df['공고상세URL']
            biz_df['amount_text'] = ''
            biz_df['amount_krw'] = None
            biz_df['stage'] = ''
            biz_df['update_type'] = '신규'
            biz_df['budget_band'] = '중간'
            biz_df['allowed_uses'] = [[] for _ in range(len(biz_df))]
            biz_df['keywords'] = [[] for _ in range(len(biz_df))]
        
        # kstartup2 데이터 정규화
        if not kstartup_df.empty:
            kstartup_df['source'] = 'K-Startup'
            kstartup_df['id'] = kstartup_df['공고일련번호'].astype(str)
            kstartup_df['title'] = kstartup_df['사업공고명']
            kstartup_df['agency'] = kstartup_df['주관기관']
            kstartup_df['region'] = kstartup_df['지원지역']
            kstartup_df['due_date'] = kstartup_df['공고접수종료일시']
            kstartup_df['info_session_date'] = kstartup_df['공고접수시작일시']
            kstartup_df['url'] = kstartup_df['상세페이지 url']
            kstartup_df['amount_text'] = ''
            kstartup_df['amount_krw'] = None
            kstartup_df['stage'] = kstartup_df['사업업력']
            kstartup_df['update_type'] = '신규'
            kstartup_df['budget_band'] = '중간'
            kstartup_df['allowed_uses'] = [[] for _ in range(len(kstartup_df))]
            kstartup_df['keywords'] = [[] for _ in range(len(kstartup_df))]
        
        # 두 데이터프레임 통합
        common_columns = ['id', 'title', 'agency', 'source', 'region', 'due_date', 
                         'info_session_date', 'url', 'amount_text', 'amount_krw', 
                         'stage', 'update_type', 'budget_band', 'allowed_uses', 'keywords']
        
        combined_df = pd.DataFrame()
        if not biz_df.empty:
            biz_selected = biz_df[common_columns]
            combined_df = pd.concat([combined_df, biz_selected], ignore_index=True)
        
        if not kstartup_df.empty:
            kstartup_selected = kstartup_df[common_columns]
            combined_df = pd.concat([combined_df, kstartup_selected], ignore_index=True)
        
        return combined_df
        
    except Exception as e:
        st.error(f"공고 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_recommendations(company_id: int = None) -> pd.DataFrame:
    """추천 데이터 로드 (recommend3 테이블 사용)"""
    try:
        query = supabase.table('recommend3').select('*')
        if company_id:
            # load_companies에서 추출한 company_name 사용
            companies_df = load_companies()
            company_data = companies_df[companies_df['id'] == company_id]
            
            if not company_data.empty and 'company_name' in company_data.columns:
                company_name = company_data.iloc[0]['company_name']
                
                # 기업명으로 recommend3에서 검색
                query = supabase.table('recommend3').select('*').ilike('company_name', f'%{company_name}%')
            else:
                # alpha_companies2의 경우 원본 ID 사용
                if company_id < 0:
                    original_id = -company_id
                    company_result = supabase.table('alpha_companies2').select('"기업명"').eq('"No."', original_id).execute()
                    if company_result.data:
                        company_name = company_result.data[0]['기업명']
                        query = supabase.table('recommend3').select('*').ilike('company_name', f'%{company_name}%')
                    else:
                        return pd.DataFrame()
                else:
                    # companies 테이블의 경우
                    company_result = supabase.table('companies').select('name').eq('id', company_id).execute()
                    if company_result.data:
                        company_name = company_result.data[0]['name']
                        query = supabase.table('recommend3').select('*').ilike('company_name', f'%{company_name}%')
                    else:
                        return pd.DataFrame()
        result = query.execute()
        return pd.DataFrame(result.data)
    except Exception as e:
        st.error(f"추천 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_recommendations2(company_id: int = None) -> pd.DataFrame:
    """추천 데이터 로드 (recommend3 테이블) - URL 정보 포함"""
    try:
        
        query = supabase.table('recommend3').select('*')
        
        # company_id가 있는 경우, 기업명으로 검색
        if company_id:
            # load_companies에서 추출한 company_name 사용
            companies_df = load_companies()
            company_data = companies_df[companies_df['id'] == company_id]
            
            if not company_data.empty and 'company_name' in company_data.columns:
                company_name = company_data.iloc[0]['company_name']
                
                # 기업명으로 recommend3에서 검색
                query = supabase.table('recommend3').select('*').ilike('company_name', f'%{company_name}%')
            else:
                # alpha_companies2의 경우 원본 ID 사용
                if company_id < 0:
                    original_id = -company_id
                    company_result = supabase.table('alpha_companies2').select('"기업명"').eq('"No."', original_id).execute()
                    if company_result.data:
                        company_name = company_result.data[0]['기업명']
                        query = supabase.table('recommend3').select('*').ilike('company_name', f'%{company_name}%')
                    else:
                        st.warning(f"회사 ID {company_id}에 대한 기업명을 찾을 수 없습니다.")
                        query = supabase.table('recommend2').select('*')
                else:
                    # companies 테이블의 경우
                    company_result = supabase.table('companies').select('name').eq('id', company_id).execute()
                    if company_result.data:
                        company_name = company_result.data[0]['name']
                        query = supabase.table('recommend3').select('*').ilike('company_name', f'%{company_name}%')
                    else:
                        st.warning(f"회사 ID {company_id}에 대한 기업명을 찾을 수 없습니다.")
                        query = supabase.table('recommend2').select('*')
        
        result = query.execute()
        df = pd.DataFrame(result.data)
        
        # company_id가 있고 데이터가 있으면 필터링
        if company_id and not df.empty and company_name:
            # 기업명으로 필터링 (클라이언트 사이드)
            if 'company_name' in df.columns:
                # 정확한 매칭 시도
                exact_match = df[df['company_name'] == company_name]
                if not exact_match.empty:
                    df = exact_match
                    st.success(f"✅ 정확한 매칭 발견: {len(exact_match)}개 추천")
                else:
                    # 부분 매칭 시도
                    partial_match = df[df['company_name'].str.contains(company_name, case=False, na=False)]
                    if not partial_match.empty:
                        df = partial_match
                        st.warning(f"⚠️ 부분 매칭 발견: {len(partial_match)}개 추천")
                    else:
                        st.warning(f"❌ 매칭되는 추천이 없습니다. 검색 기업명: {company_name}")
                        # 디버깅을 위해 recommend3의 기업명 샘플 표시
                        sample_companies = df['company_name'].unique()[:5]
                        st.info(f"📋 recommend3 테이블 기업명 샘플: {list(sample_companies)}")
            elif '기업명' in df.columns:
                df = df[df['기업명'].str.contains(company_name, case=False, na=False)]
        
        # 컬럼명을 한국어로 매핑 (recommend3 테이블에 맞게)
        if not df.empty:
            # recommend3 테이블의 컬럼명에 맞게 매핑
            column_mapping = {
                'company_name': '회사명',
                'title_y': '공고제목',
                'source': '공고출처',
                'final_score': '총점수',
                'final_level': '적합도',
                'description': '매칭이유',
                'apply_start_y': '접수시작일',
                'apply_end_y': '접수마감일',
                'url': '공고보기',
                'doc_text': '공고상세정보'
            }
            
            # 존재하는 컬럼만 매핑
            existing_columns = df.columns.tolist()
            mapping_to_apply = {k: v for k, v in column_mapping.items() if k in existing_columns}
            df = df.rename(columns=mapping_to_apply)
            
            # status 컬럼이 없으면 기본값 'pending'으로 설정
            if 'status' not in df.columns:
                df['status'] = 'pending'
                
                # 세션 상태에서 상태 정보 가져오기
                if 'recommendation_status' in st.session_state:
                    for idx, row in df.iterrows():
                        company_name = row.get('company_name', '')
                        announcement_title = row.get('title_y', '')
                        if company_name and announcement_title:
                            key = f"{company_name}_{announcement_title}"
                            if key in st.session_state['recommendation_status']:
                                df.at[idx, 'status'] = st.session_state['recommendation_status'][key]
            
            # 지원가능여부 컬럼 추가 (매핑 후 컬럼명 사용)
            if '접수시작일' in df.columns and '접수마감일' in df.columns:
                df['지원가능여부'] = df.apply(
                    lambda row: calculate_support_status(row['접수시작일'], row['접수마감일']), 
                    axis=1
                )
        
        return df
    except Exception as e:
        st.error(f"추천 데이터 로드 실패 (recommend2): {e}")
        return pd.DataFrame()

def update_recommendation_status(company_name, announcement_title, status):
    """추천 공고의 승인/반려 상태 업데이트"""
    if supabase is None:
        st.warning("Supabase 연결이 없습니다. 데모 모드로 실행됩니다.")
        return False
    
    try:
        # 세션 상태 초기화
        if 'recommendation_status' not in st.session_state:
            st.session_state['recommendation_status'] = {}
        
        # 세션 상태에 저장 (항상 세션 상태로 관리)
        key = f"{company_name}_{announcement_title}"
        st.session_state['recommendation_status'][key] = status
        
        # 데이터베이스에도 업데이트 시도 (status 컬럼이 있는 경우)
        try:
            result = supabase.table('recommend3').select('*').eq('company_name', company_name).eq('title_y', announcement_title).execute()
            
            if result.data and 'status' in result.data[0]:
                update_data = {'status': status}
                supabase.table('recommend3').update(update_data).eq('company_name', company_name).eq('title_y', announcement_title).execute()
        except:
            pass
        
        return True
            
    except Exception as e:
        st.error(f"❌ 상태 업데이트 실패: {e}")
        return False

def get_recommendation_status(company_name, announcement_title):
    """추천 공고의 현재 상태 조회"""
    # 세션 상태 초기화
    if 'recommendation_status' not in st.session_state:
        st.session_state['recommendation_status'] = {}
    
    # 세션 상태에서 먼저 확인
    key = f"{company_name}_{announcement_title}"
    if key in st.session_state['recommendation_status']:
        return st.session_state['recommendation_status'][key]
    
    # 세션 상태에 없으면 데이터베이스에서 확인
    if supabase is not None:
        try:
            result = supabase.table('recommend3').select('status').eq('company_name', company_name).eq('title_y', announcement_title).execute()
            
            if result.data and len(result.data) > 0:
                status = result.data[0].get('status', 'pending')
                # 데이터베이스에서 가져온 상태를 세션 상태에도 저장
                st.session_state['recommendation_status'][key] = status
                return status
        except:
            pass
    
    return 'pending'

def create_recommend3_table():
    """recommend3 테이블 생성"""
    try:
        # recommend3 테이블 생성 SQL
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS recommend3 (
            id SERIAL PRIMARY KEY,
            company_id INTEGER,
            company_name VARCHAR(255),
            announcement_title TEXT,
            announcement_source VARCHAR(100),
            total_score DECIMAL(5,2),
            matching_reason TEXT,
            application_start_date DATE,
            application_end_date DATE,
            detail_page_url TEXT,
            announcement_details TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # 테이블 생성 실행
        result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        st.info("✅ recommend3 테이블이 생성되었습니다.")
        
        # 인덱스 생성
        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_recommend3_company_id ON recommend3(company_id);
        CREATE INDEX IF NOT EXISTS idx_recommend3_company_name ON recommend3(company_name);
        CREATE INDEX IF NOT EXISTS idx_recommend3_total_score ON recommend3(total_score);
        """
        
        supabase.rpc('exec_sql', {'sql': index_sql}).execute()
        
    except Exception as e:
        st.warning(f"recommend3 테이블 생성 중 오류: {e}")
        # 테이블이 이미 존재하는 경우 무시

def load_recommendations_region4(company_id: int = None) -> pd.DataFrame:
    """지역별 추천 데이터 로드 (recommend_region4 테이블)"""
    try:
        query = supabase.table('recommend_region4').select('*')
        if company_id:
            # alpha_companies2 테이블에서 기업명 찾기
            company_name = None
            try:
                # company_id가 음수인 경우 (alpha_companies2에서 온 경우)
                if company_id < 0:
                    original_id = -company_id
                    alpha_result = supabase.table('alpha_companies2').select('"기업명"').eq('"No."', original_id).execute()
                else:
                    # company_id가 양수인 경우 (companies 테이블에서 온 경우)
                    alpha_result = supabase.table('alpha_companies2').select('"기업명"').eq('"No."', company_id).execute()
                
                if alpha_result.data:
                    company_name = alpha_result.data[0]['기업명']
            except:
                pass
            
            if company_name:
                # 기업명으로 recommend_region4에서 부분 매칭 (ilike 사용)
                query = supabase.table('recommend_region4').select('*').ilike('company_name', f'%{company_name}%')
        
        result = query.execute()
        df = pd.DataFrame(result.data)
        
        # 컬럼명을 한국어로 매핑 (recommend_region4 테이블에 맞게)
        if not df.empty:
            column_mapping = {
                'company_name': '회사명',
                'company_province': '회사지역',
                'program_id': '프로그램ID',
                'url': '공고보기',
                'final_score': '총점수',
                'final_score_10': '총점수(10점만점)',
                'final_level': '적합도',
                'program_provinces': '프로그램지역',
                'region_match': '지역매칭',
                'source': '공고출처',
                'base_score': '기본점수',
                'sim_raw': '유사도(원본)',
                'sim_points': '유사도점수',
                'priority_boost_points': '우선순위보너스',
                'base_score_10': '기본점수(10점만점)',
                'score_stage': '단계점수',
                'score_industry': '업종점수',
                'score_region': '지역점수',
                'score_timing': '시기점수',
                'score_bonus': '보너스점수',
                'score_penalty': '감점',
                'priority_type_x': '우선순위유형',
                'title_x': '공고제목',
                'sim': '유사도',
                'apply_start_x': '접수시작일',
                'apply_end_x': '접수마감일',
                'region': '지역',
                'years': '업력',
                'raw_text': '원본텍스트',
                'industry_primary': '주요업종',
                'title_y': '프로그램제목',
                'description': '프로그램설명',
                'category': '카테고리',
                'doc_text': '문서텍스트',
                'program_region': '프로그램지역',
                'priority_type_y': '우선순위유형2',
                'apply_start_y': '접수시작일2',
                'apply_end_y': '접수마감일2',
                'base_score_recomputed': '재계산기본점수',
                'region_prog': '프로그램지역2',
                'title_prog': '프로그램제목2',
                'description_prog': '프로그램설명2',
                'category_prog': '카테고리2',
                'doc_text_prog': '문서텍스트2'
            }
            
            # 존재하는 컬럼만 매핑
            existing_columns = df.columns.tolist()
            mapping_to_apply = {k: v for k, v in column_mapping.items() if k in existing_columns}
            df = df.rename(columns=mapping_to_apply)
        
        # 지원가능여부 컬럼 추가
        if not df.empty and '접수시작일' in df.columns and '접수마감일' in df.columns:
            df['지원가능여부'] = df.apply(
                lambda row: calculate_support_status(row['접수시작일'], row['접수마감일']), 
                axis=1
            )
        
        return df
    except Exception as e:
        st.error(f"지역별 추천 데이터 로드 실패 (recommend_region4): {e}")
        return pd.DataFrame()

def load_recommendations_rules4(company_id: int = None) -> pd.DataFrame:
    """규칙별 추천 데이터 로드 (recommend_rules4 테이블)"""
    try:
        query = supabase.table('recommend_rules4').select('*')
        if company_id:
            # alpha_companies2 테이블에서 기업명 찾기
            company_name = None
            try:
                # company_id가 음수인 경우 (alpha_companies2에서 온 경우)
                if company_id < 0:
                    original_id = -company_id
                    alpha_result = supabase.table('alpha_companies2').select('"기업명"').eq('"No."', original_id).execute()
                else:
                    # company_id가 양수인 경우 (companies 테이블에서 온 경우)
                    alpha_result = supabase.table('alpha_companies2').select('"기업명"').eq('"No."', company_id).execute()
                
                if alpha_result.data:
                    company_name = alpha_result.data[0]['기업명']
            except Exception as e:
                pass
            
            if company_name:
                # 기업명으로 recommend_rules4에서 부분 매칭 (ilike 사용)
                query = supabase.table('recommend_rules4').select('*').ilike('company_name', f'%{company_name}%')
        
        result = query.execute()
        df = pd.DataFrame(result.data)
        
        # 컬럼명을 한국어로 매핑 (recommend_rules4 테이블의 실제 컬럼명에 맞게)
        if not df.empty:
            column_mapping = {
                'company_id': '회사ID',
                'company_name': '회사명',
                'company_province': '회사지역',
                'company_years': '회사업력',
                'company_section': '회사업종',
                'program_id': '프로그램ID',
                'priority_type': '우선순위유형',
                'title': '공고제목',
                'url': '공고보기',
                'apply_start': '접수시작일',
                'apply_end': '접수마감일',
                'program_provinces': '프로그램지역',
                'program_years_min': '최소업력',
                'program_years_max': '최대업력',
                'program_section': '프로그램업종',
                'passed': '통과여부',
                'reason': '통과이유'
            }
            
            # 존재하는 컬럼만 매핑
            existing_columns = df.columns.tolist()
            mapping_to_apply = {k: v for k, v in column_mapping.items() if k in existing_columns}
            df = df.rename(columns=mapping_to_apply)
        
        # 지원가능여부 컬럼 추가
        if not df.empty and '접수시작일' in df.columns and '접수마감일' in df.columns:
            df['지원가능여부'] = df.apply(
                lambda row: calculate_support_status(row['접수시작일'], row['접수마감일']), 
                axis=1
            )
        
        return df
    except Exception as e:
        st.error(f"규칙별 추천 데이터 로드 실패 (recommend_rules4): {e}")
        return pd.DataFrame()

def load_recommendations_priority4(company_id: int = None) -> pd.DataFrame:
    """3대장별 추천 데이터 로드 (recommend_priority4 테이블)"""
    try:
        query = supabase.table('recommend_priority4').select('*')
        if company_id:
            # alpha_companies2 테이블에서 기업명 찾기
            company_name = None
            try:
                # company_id가 음수인 경우 (alpha_companies2에서 온 경우)
                if company_id < 0:
                    original_id = -company_id
                    alpha_result = supabase.table('alpha_companies2').select('"기업명"').eq('"No."', original_id).execute()
                else:
                    # company_id가 양수인 경우 (companies 테이블에서 온 경우)
                    alpha_result = supabase.table('alpha_companies2').select('"기업명"').eq('"No."', company_id).execute()
                
                if alpha_result.data:
                    company_name = alpha_result.data[0]['기업명']
            except:
                pass
            
            if company_name:
                # 기업명으로 recommend_priority4에서 부분 매칭 (ilike 사용)
                query = supabase.table('recommend_priority4').select('*').ilike('company_name', f'%{company_name}%')
        
        result = query.execute()
        df = pd.DataFrame(result.data)
        
        # 컬럼명을 한국어로 매핑 (recommend_priority4 테이블의 실제 컬럼명에 맞게)
        if not df.empty:
            column_mapping = {
                'company_id': '회사ID',
                'company_name': '회사명',
                'program_id': '프로그램ID',
                'source': '공고출처',
                'final_score': '총점수',
                'base_score': '기본점수',
                'sim_raw': '유사도(원본)',
                'sim_points': '유사도점수',
                'priority_boost_points': '우선순위보너스',
                'final_score_10': '총점수(10점만점)',
                'base_score_10': '기본점수(10점만점)',
                'final_level': '적합도',
                'score_stage': '단계점수',
                'score_industry': '업종점수',
                'score_region': '지역점수',
                'score_timing': '시기점수',
                'score_bonus': '보너스점수',
                'score_penalty': '감점',
                'url': '공고보기',
                'priority_type_x': '우선순위유형',
                'title_x': '공고제목',
                'sim': '유사도',
                'apply_start_x': '접수시작일',
                'apply_end_x': '접수마감일',
                'region': '지역',
                'years': '업력',
                'raw_text': '원본텍스트',
                'industry_primary': '주요업종',
                'title_y': '프로그램제목',
                'description': '프로그램설명',
                'category': '카테고리',
                'doc_text': '문서텍스트',
                'program_region': '프로그램지역',
                'priority_type_y': '우선순위유형2',
                'apply_start_y': '접수시작일2',
                'apply_end_y': '접수마감일2',
                'base_score_recomputed': '재계산기본점수'
            }
            
            # 존재하는 컬럼만 매핑
            existing_columns = df.columns.tolist()
            mapping_to_apply = {k: v for k, v in column_mapping.items() if k in existing_columns}
            df = df.rename(columns=mapping_to_apply)
        
        # 지원가능여부 컬럼 추가
        if not df.empty and '접수시작일' in df.columns and '접수마감일' in df.columns:
            df['지원가능여부'] = df.apply(
                lambda row: calculate_support_status(row['접수시작일'], row['접수마감일']), 
                axis=1
            )
        
        return df
    except Exception as e:
        st.error(f"3대장별 추천 데이터 로드 실패 (recommend_priority4): {e}")
        return pd.DataFrame()

def load_recommendations_keyword4(company_id: int = None) -> pd.DataFrame:
    """키워드별 추천 데이터 로드 (recommend_keyword4 테이블)"""
    try:
        query = supabase.table('recommend_keyword4').select('*')
        if company_id:
            # alpha_companies2 테이블에서 기업명 찾기
            company_name = None
            try:
                # company_id가 음수인 경우 (alpha_companies2에서 온 경우)
                if company_id < 0:
                    original_id = -company_id
                    alpha_result = supabase.table('alpha_companies2').select('"기업명"').eq('"No."', original_id).execute()
                else:
                    # company_id가 양수인 경우 (companies 테이블에서 온 경우)
                    alpha_result = supabase.table('alpha_companies2').select('"기업명"').eq('"No."', company_id).execute()
                
                if alpha_result.data:
                    company_name = alpha_result.data[0]['기업명']
            except:
                pass
            
            if company_name:
                # 기업명으로 recommend_keyword4에서 부분 매칭 (ilike 사용)
                query = supabase.table('recommend_keyword4').select('*').ilike('company_name', f'%{company_name}%')
        
        result = query.execute()
        df = pd.DataFrame(result.data)
        
        # 컬럼명을 한국어로 매핑 (recommend_keyword4 테이블의 실제 컬럼명에 맞게)
        if not df.empty:
            column_mapping = {
                'company_name': '회사명',
                'program_id': '프로그램ID',
                'url': '공고보기',
                'title': '공고제목',
                'priority_type': '우선순위유형',
                'apply_start': '접수시작일',
                'apply_end': '접수마감일',
                'kw_intersection': '키워드교집합',
                'kw_tfidf': '키워드TF-IDF',
                'kw_bm25': '키워드BM25',
                'kw_phrase_hit': '키워드구문매칭',
                'kw_must_have_hits': '필수키워드매칭',
                'kw_forbid_hit': '금지키워드매칭',
                'kw_gate': '키워드게이트',
                'kw_reason': '키워드매칭이유',
                'keyword_points': '키워드점수'
            }
            
            # 존재하는 컬럼만 매핑
            existing_columns = df.columns.tolist()
            mapping_to_apply = {k: v for k, v in column_mapping.items() if k in existing_columns}
            df = df.rename(columns=mapping_to_apply)
        
        # 지원가능여부 컬럼 추가
        if not df.empty and '접수시작일' in df.columns and '접수마감일' in df.columns:
            df['지원가능여부'] = df.apply(
                lambda row: calculate_support_status(row['접수시작일'], row['접수마감일']), 
                axis=1
            )
        
        return df
    except Exception as e:
        st.error(f"키워드별 추천 데이터 로드 실패 (recommend_keyword4): {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_recommendations3_active(company_id: int = None) -> pd.DataFrame:
    """활성 추천 데이터 로드 (recommend_active3 테이블) - URL 정보 포함"""
    try:
        query = supabase.table('recommend_active3').select('*')
        if company_id:
            # 회사의 기업명으로 직접 매칭
            company_name = None
            
            # companies 테이블에서 먼저 찾기
            try:
                company_result = supabase.table('companies').select('name').eq('id', company_id).execute()
                if company_result.data:
                    company_name = company_result.data[0]['name']
            except:
                pass
            
            # alpha_companies2 테이블에서 찾기
            if not company_name:
                try:
                    alpha_result = supabase.table('alpha_companies2').select('"기업명"').eq('"No."', company_id).execute()
                    if alpha_result.data:
                        company_name = alpha_result.data[0]['기업명']
                except:
                    pass
            
            if company_name:
                # 기업명으로 recommend_active3에서 검색
                query = supabase.table('recommend_active3').select('*').ilike('company_name', f'%{company_name}%')
        result = query.execute()
        df = pd.DataFrame(result.data)
        
        # 컬럼명을 한국어로 매핑 (recommend_active3 테이블에 맞게)
        if not df.empty:
            column_mapping = {
                'company_name': '회사명',
                'title': '공고제목',
                'source': '공고출처',
                'final_score': '총점수',
                'url': '공고보기',
                'apply_start': '접수시작일',
                'apply_end': '접수마감일'
            }
            
            # 존재하는 컬럼만 매핑
            existing_columns = df.columns.tolist()
            mapping_to_apply = {k: v for k, v in column_mapping.items() if k in existing_columns}
            df = df.rename(columns=mapping_to_apply)
        
        # 지원가능여부 컬럼 추가
        if not df.empty and '접수시작일' in df.columns and '접수마감일' in df.columns:
            df['지원가능여부'] = df.apply(
                lambda row: calculate_support_status(row['접수시작일'], row['접수마감일']), 
                axis=1
            )
        
        return df
    except Exception as e:
        st.error(f"활성 추천 데이터 로드 실패 (recommend_active3): {e}")
        return pd.DataFrame()

def save_company(company_data: Dict) -> bool:
    """회사 저장"""
    try:
        if supabase is None:
            st.warning("데모 모드에서는 회사 저장이 불가능합니다.")
            return False
        
        result = supabase.table('companies').insert(company_data).execute()
        return True
    except Exception as e:
        st.error(f"회사 저장 실패: {e}")
        return False

def delete_company(company_id: int) -> bool:
    """회사 삭제"""
    try:
        if supabase is None:
            st.warning("데모 모드에서는 회사 삭제가 불가능합니다.")
            return False
        
        supabase.table('companies').delete().eq('id', company_id).execute()
        return True
    except Exception as e:
        st.error(f"회사 삭제 실패: {e}")
        return False

def enhanced_save_company_with_recommendations(company_data: Dict) -> bool:
    """신규 회사 추가 및 자동 추천 생성"""
    try:
        # 1. 회사 데이터를 companies 테이블에 저장
        company_insert_data = {
            'name': company_data['name'],
            'business_type': company_data['business_type'],
            'region': company_data['region'],
            'years': company_data.get('years', 0),
            'stage': company_data.get('stage', '예비'),
            'industry': company_data['industry'],
            'keywords': company_data.get('keywords', []),
            'preferred_uses': company_data.get('preferred_uses', []),
            'preferred_budget': company_data.get('preferred_budget', '소액')
        }
        
        # 회사 저장
        result = supabase.table('companies').insert(company_insert_data).execute()
        
        if not result.data:
            st.error("회사 저장 실패")
            return False
        
        # 저장된 회사의 ID 가져오기
        company_id = result.data[0]['id']
        
        # 2. 자동 추천 생성
        recommendations = generate_company_recommendations(company_data, company_id)
        
        if recommendations:
            # 3. 추천 결과를 recommend3 테이블에 저장
            save_recommendations_to_supabase(company_id, recommendations)
            
            # 4. 알림 상태 초기화
            initialize_notification_state(company_id)
            
            st.success(f"✅ 회사가 추가되었습니다! (ID: {company_id})")
            st.success(f"🎯 {len(recommendations)}개의 맞춤 추천이 생성되었습니다!")
            
            return True
        else:
            st.warning("회사는 추가되었지만 추천 생성에 실패했습니다.")
            return True
            
    except Exception as e:
        st.error(f"회사 추가 및 추천 생성 실패: {e}")
        return False

def generate_company_recommendations(company_data: Dict, company_id: int) -> List[Dict]:
    """신규 회사에 대한 맞춤 추천 생성"""
    try:
        recommendations = []
        
        # 1. biz2 데이터에서 추천 생성
        biz_recommendations = generate_biz_recommendations(company_data, company_id)
        recommendations.extend(biz_recommendations)
        
        # 2. kstartup2 데이터에서 추천 생성
        kstartup_recommendations = generate_kstartup_recommendations(company_data, company_id)
        recommendations.extend(kstartup_recommendations)
        
        # 3. 추천 결과 정렬 및 중복 제거
        recommendations = deduplicate_and_sort_recommendations(recommendations)
        
        return recommendations[:20]  # 상위 20개만 반환
        
    except Exception as e:
        st.error(f"추천 생성 실패: {e}")
        return []

def generate_biz_recommendations(company_data: Dict, company_id: int) -> List[Dict]:
    """기업마당(biz2) 데이터 기반 추천 생성"""
    try:
        # biz2 데이터 로드
        result = supabase.table('biz2').select('*').execute()
        if not result.data:
            return []
        
        biz_df = pd.DataFrame(result.data)
        recommendations = []
        
        # 업종 매칭
        industry = company_data.get('industry', '')
        keywords = company_data.get('keywords', [])
        
        for _, announcement in biz_df.iterrows():
            score = 0
            matching_reasons = []
            
            # 업종 매칭
            if industry and '지원분야' in announcement:
                if industry in str(announcement['지원분야']):
                    score += 80
                    matching_reasons.append(f"업종 매칭: {industry}")
            
            # 키워드 매칭
            for keyword in keywords:
                if keyword and '공고명' in announcement:
                    if keyword in str(announcement['공고명']):
                        score += 70
                        matching_reasons.append(f"키워드 매칭: {keyword}")
                        break
            
            # 지역 매칭
            region = company_data.get('region', '')
            if region and '소관부처' in announcement:
                if region in str(announcement['소관부처']):
                    score += 60
                    matching_reasons.append(f"지역 매칭: {region}")
            
            if score > 0:
                recommendations.append({
                    'company_id': company_id,
                    'company_name': company_data['name'],
                    'announcement_title': announcement.get('공고명', ''),
                    'announcement_source': '기업마당',
                    'total_score': score,
                    'matching_reason': '; '.join(matching_reasons),
                    'application_start_date': announcement.get('신청시작일자', ''),
                    'application_end_date': announcement.get('신청종료일자', ''),
                    'detail_page_url': announcement.get('공고상세URL', ''),
                    'announcement_details': f"소관부처: {announcement.get('소관부처', 'N/A')}, 사업수행기관: {announcement.get('사업수행기관', 'N/A')}",
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
        
        return recommendations
        
    except Exception as e:
        st.error(f"biz2 추천 생성 실패: {e}")
        return []

def generate_kstartup_recommendations(company_data: Dict, company_id: int) -> List[Dict]:
    """K-스타트업(kstartup2) 데이터 기반 추천 생성"""
    try:
        # kstartup2 데이터 로드
        result = supabase.table('kstartup2').select('*').execute()
        if not result.data:
            return []
        
        kstartup_df = pd.DataFrame(result.data)
        recommendations = []
        
        # 업종 및 키워드 매칭
        industry = company_data.get('industry', '')
        keywords = company_data.get('keywords', [])
        
        for _, announcement in kstartup_df.iterrows():
            score = 0
            matching_reasons = []
            
            # 업종 매칭
            if industry and '지원사업분류' in announcement:
                if industry in str(announcement['지원사업분류']):
                    score += 80
                    matching_reasons.append(f"업종 매칭: {industry}")
            
            # 키워드 매칭 (공고내용에서)
            for keyword in keywords:
                if keyword and '공고내용' in announcement:
                    if keyword in str(announcement['공고내용']):
                        score += 70
                        matching_reasons.append(f"키워드 매칭: {keyword}")
                        break
            
            # 사업아이템 매칭
            if 'description' in company_data:
                business_item = company_data['description']
                if business_item and '공고내용' in announcement:
                    if business_item in str(announcement['공고내용']):
                        score += 90
                        matching_reasons.append("사업아이템 매칭")
            
            if score > 0:
                recommendations.append({
                    'company_id': company_id,
                    'company_name': company_data['name'],
                    'announcement_title': announcement.get('사업공고명', ''),
                    'announcement_source': 'K-스타트업',
                    'total_score': score,
                    'matching_reason': '; '.join(matching_reasons),
                    'application_start_date': announcement.get('공고접수시작일시', ''),
                    'application_end_date': announcement.get('공고접수종료일시', ''),
                    'detail_page_url': announcement.get('상세페이지 url', ''),
                    'announcement_details': announcement.get('공고내용', '')[:200] + '...' if len(str(announcement.get('공고내용', ''))) > 200 else announcement.get('공고내용', ''),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
        
        return recommendations
        
    except Exception as e:
        st.error(f"kstartup2 추천 생성 실패: {e}")
        return []

def deduplicate_and_sort_recommendations(recommendations: List[Dict]) -> List[Dict]:
    """추천 결과 중복 제거 및 정렬"""
    try:
        # 중복 제거 (공고제목 기준)
        seen = set()
        unique_recommendations = []
        
        for rec in recommendations:
            key = (rec['company_id'], rec['announcement_title'])
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)
        
        # 점수 기준으로 정렬
        unique_recommendations.sort(key=lambda x: x['total_score'], reverse=True)
        
        return unique_recommendations
        
    except Exception as e:
        st.error(f"추천 정렬 실패: {e}")
        return recommendations

def save_recommendations_to_supabase(company_id: int, recommendations: List[Dict]):
    """추천 결과를 Supabase에 저장"""
    try:
        for rec in recommendations:
            rec['company_id'] = company_id
            supabase.table('recommend3').insert(rec).execute()
        
        st.info(f"📊 {len(recommendations)}개 추천이 recommend3 테이블에 저장되었습니다.")
        
    except Exception as e:
        st.error(f"추천 저장 실패: {e}")

def initialize_notification_state(company_id: int):
    """알림 상태 초기화"""
    try:
        notification_data = {
            'company_id': company_id,
            'last_seen_announcement_ids': [],
            'last_updated': datetime.now().isoformat()
        }
        
        supabase.table('notification_states').insert(notification_data).execute()
        st.info(f"🔔 알림 상태가 초기화되었습니다.")
        
    except Exception as e:
        st.error(f"알림 상태 초기화 실패: {e}")

def delete_company(company_id: int) -> bool:
    """회사 삭제"""
    try:
        supabase.table('companies').delete().eq('id', company_id).execute()
        return True
    except Exception as e:
        st.error(f"회사 삭제 실패: {e}")
        return False

@st.cache_data(ttl=300)  # 5분 캐싱
def load_notifications(company_id: int) -> List[str]:
    """알림 상태 로드"""
    try:
        # alpha_companies2의 음수 ID는 세션 상태에서 로드
        if company_id < 0:
            if 'notification_states' in st.session_state and company_id in st.session_state['notification_states']:
                return st.session_state['notification_states'][company_id].get('last_seen_announcement_ids', [])
            return []
        
        # 양수 ID는 데이터베이스에서 로드
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
        # alpha_companies2의 음수 ID는 notification_states 테이블에 저장하지 않음
        if company_id < 0:
            # 음수 ID는 세션 상태로만 관리
            if 'notification_states' not in st.session_state:
                st.session_state['notification_states'] = {}
            
            st.session_state['notification_states'][company_id] = {
                'last_seen_announcement_ids': announcement_ids,
                'last_updated': datetime.now().isoformat()
            }
            return True
        
        # 양수 ID만 데이터베이스에 저장
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
            if 'company_name' in companies_df.columns:
                # 기업명으로 검색
                filtered_companies = companies_df[
                    companies_df['company_name'].str.contains(search_term, case=False, na=False)
                ]
            else:
                # 기존 방식으로 검색
                filtered_companies = companies_df[
                    companies_df['name'].str.contains(search_term, case=False, na=False)
                ]
        else:
            filtered_companies = companies_df
        
        # 회사 선택 (기업명 + 사업 아이템으로 표시)
        if 'company_name' in filtered_companies.columns:
            # 기업명이 있는 경우 기업명 + 사업 아이템으로 표시
            company_display_names = filtered_companies['company_name'].tolist()
            company_descriptions = filtered_companies['name'].tolist()  # 사업아이템 한 줄 소개
            company_ids = filtered_companies['id'].tolist()
            source_tables = filtered_companies.get('source_table', [''] * len(company_display_names)).tolist()
            
            if company_display_names:
                # 신규 회사 구분하여 표시
                display_options = []
                for name, desc, id, source in zip(company_display_names, company_descriptions, company_ids, source_tables):
                    if source == 'companies' or id > 0:  # 신규 회사 (companies 테이블 또는 양수 ID)
                        display_options.append(f"🆕 신규 {name} - {desc}")
                    else:  # 기존 회사 (alpha_companies2 테이블 또는 음수 ID)
                        display_options.append(f"{name} - {desc}")
                
                selected_display = st.sidebar.selectbox(
                    "회사 선택",
                    display_options,
                    key="existing_company_select"
                )
                if selected_display:
                    # 선택된 기업명 추출 (🆕 신규 표시 제거)
                    selected_company_name = selected_display.replace("🆕 신규 ", "").split(" - ")[0]
                    selected_company_data = filtered_companies[filtered_companies['company_name'] == selected_company_name].iloc[0]
                    st.session_state['selected_company'] = selected_company_data.to_dict()
            else:
                st.sidebar.info("검색 결과가 없습니다.")
        else:
            # 기업명이 없는 경우 기존 방식 사용
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
                
                if enhanced_save_company_with_recommendations(company_data):
                    st.rerun()
            else:
                st.error("회사명을 입력해주세요.")


def render_alerts_tab():
    """신규 공고 알림 탭 렌더링 (recommendations3 테이블 사용)"""
    if 'selected_company' not in st.session_state:
        st.info("사이드바에서 회사를 선택해주세요.")
        return
    
    company = st.session_state['selected_company']
    display_name = company.get('company_name', company.get('name', 'Unknown'))
    st.subheader(f"🔔 {display_name} 신규 공고 알림")
    
    # 회사가 바뀌면 확인 상태 초기화
    if 'last_selected_company' not in st.session_state:
        st.session_state['last_selected_company'] = company['id']
    elif st.session_state['last_selected_company'] != company['id']:
        st.session_state['notifications_processed'] = False
        st.session_state['last_selected_company'] = company['id']
        # 개별 확인 상태도 초기화
        st.session_state['individual_seen_announcements'] = []
    
    # 알림 상태 로드
    last_seen_ids = load_notifications(company['id'])
    
    # 활성 추천 데이터 로드 (recommend3 테이블 사용) - 캐싱된 데이터 사용
    recommendations2_df = load_recommendations2(company['id'])
    
    if not recommendations2_df.empty:
        # 중복 제거: 공고명별로 가장 높은 총점수를 가진 레코드만 유지
        if '공고제목' in recommendations2_df.columns and '총점수' in recommendations2_df.columns:
            recommendations2_df = recommendations2_df.sort_values('총점수', ascending=False).drop_duplicates(subset=['공고제목'], keep='first')
            recommendations2_df = recommendations2_df.sort_values('총점수', ascending=False)
        
        # 활성 공고만 필터링 (마감일 기준) - 최적화된 필터링
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')
        
        # 접수마감일이 있는 경우만 필터링
        if '접수마감일' in recommendations2_df.columns:
            active_recommendations = recommendations2_df[
                (recommendations2_df['접수마감일'] >= today_str) |
                (recommendations2_df['접수마감일'].isna())
            ]
        else:
            active_recommendations = recommendations2_df
        
        if not active_recommendations.empty:
            # 확인 처리된 공고 필터링
            last_seen_names = []
            if last_seen_ids:
                # 기존 알림 상태에서 공고 이름들을 가져옴
                last_seen_names = last_seen_ids
            
            # 개별 확인된 공고도 추가
            individual_seen = st.session_state.get('individual_seen_announcements', [])
            for name in individual_seen:
                if name not in last_seen_names:
                    last_seen_names.append(name)
            
            # 확인 처리되지 않은 공고만 필터링
            if last_seen_names:
                # 공고제목이 last_seen_names에 없는 것만 선택
                new_announcements = active_recommendations[
                    ~active_recommendations['공고제목'].isin(last_seen_names)
                ]
            else:
                # 확인 처리된 공고가 없으면 모든 활성 공고를 신규로 표시
                new_announcements = active_recommendations
            
            # 확인 처리 버튼이 눌렸는지 확인
            if 'notifications_processed' not in st.session_state:
                st.session_state['notifications_processed'] = False
            
            # 숨김 처리된 공고들 표시 (상단)
            if last_seen_names:
                with st.expander(f"📋 숨김 처리된 공고 ({len(last_seen_names)}개)", expanded=False):
                    # 숨김 처리된 공고들을 원본 데이터에서 찾아서 표시
                    hidden_announcements = active_recommendations[
                        active_recommendations['공고제목'].isin(last_seen_names)
                    ]
                    
                    if not hidden_announcements.empty:
                        for idx, row in hidden_announcements.iterrows():
                            with st.container():
                                col1, col2, col3 = st.columns([3, 1, 1])
                                
                                with col1:
                                    st.write(f"~~{row.get('공고제목', 'N/A')}~~")  # 취소선으로 표시
                                    if '기관명' in row and pd.notna(row['기관명']):
                                        st.caption(f"📋 {row['기관명']}")
                                    if '매칭이유' in row and pd.notna(row['매칭이유']):
                                        st.caption(f"💡 {row['매칭이유']}")
                                
                                with col2:
                                    if '총점수' in row and pd.notna(row['총점수']):
                                        st.metric("점수", f"{row['총점수']:.0f}")
                                    if '적합도' in row and pd.notna(row['적합도']):
                                        st.caption(f"적합도: {row['적합도']}")
                                
                                with col3:
                                    if '접수마감일' in row and pd.notna(row['접수마감일']):
                                        st.caption(f"마감: {row['접수마감일']}")
                                    if '공고보기' in row and pd.notna(row['공고보기']):
                                        st.link_button("공고보기", row['공고보기'])
                                
                                st.divider()
                    
                    # 새로고침 버튼
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("🔄 새로고침", use_container_width=True):
                            # 모든 확인 상태 초기화
                            st.session_state['notifications_processed'] = False
                            st.session_state['individual_seen_announcements'] = []
                            # 개별 공고 확인 상태도 초기화
                            for key in list(st.session_state.keys()):
                                if key.startswith(f"announcement_{company['id']}_"):
                                    del st.session_state[key]
                            st.rerun()
                
                st.markdown("---")
            
            # 신규 공고가 있는 경우
            if not new_announcements.empty:
                # 상단 헤더 영역 - 공고 개수와 버튼을 같은 줄에 배치
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.success(f"🆕 {len(new_announcements)}개의 신규 공고가 있습니다!")
                
                with col2:
                    # 모두 확인 처리 버튼 - 상단 오른쪽 고정
                    if st.button("✅ 모두 확인 처리", type="primary", use_container_width=True):
                        # 현재 신규 공고들의 공고제목을 스냅샷에 저장
                        current_names = new_announcements['공고제목'].tolist()
                        
                        # 기존 개별 확인된 공고와 합치기
                        individual_seen = st.session_state.get('individual_seen_announcements', [])
                        all_names = list(set(current_names + individual_seen))
                        
                        if save_notifications(company['id'], all_names):
                            # 모든 공고를 개별 확인 상태로 설정
                            for name in current_names:
                                announcement_key = f"announcement_{company['id']}_{name}"
                                st.session_state[announcement_key] = True
                            
                            # 개별 확인 목록 업데이트
                            st.session_state['individual_seen_announcements'] = all_names
                            
                            st.rerun()
                        else:
                            st.error("❌ 확인 처리에 실패했습니다.")
                
                # 구분선
                st.markdown("---")
                
                # 스크롤 가능한 공고 목록 영역
                st.markdown("""
                <style>
                .scrollable-container {
                    max-height: 60vh;
                    overflow-y: auto;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 1rem;
                    background-color: #fafafa;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # 공고 목록을 스크롤 가능한 컨테이너로 감싸기
                with st.container():
                    st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
                    
                    # 공고 목록을 간단한 카드 형태로 표시
                    for idx, row in new_announcements.iterrows():
                        announcement_name = row.get('공고제목', 'N/A')
                        
                        # 개별 공고 확인 상태 관리 (공고명 기반)
                        announcement_key = f"announcement_{company['id']}_{announcement_name}"
                        
                        # 이미 확인된 공고는 건너뛰기
                        if st.session_state.get(announcement_key, False):
                            continue
                            
                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                            
                            with col1:
                                st.write(f"**{announcement_name}**")
                                if '기관명' in row and pd.notna(row['기관명']):
                                    st.caption(f"📋 {row['기관명']}")
                                if '매칭이유' in row and pd.notna(row['매칭이유']):
                                    st.caption(f"💡 {row['매칭이유']}")
                            
                            with col2:
                                if '총점수' in row and pd.notna(row['총점수']):
                                    st.metric("점수", f"{row['총점수']:.0f}")
                                if '적합도' in row and pd.notna(row['적합도']):
                                    st.caption(f"적합도: {row['적합도']}")
                            
                            with col3:
                                if '접수마감일' in row and pd.notna(row['접수마감일']):
                                    st.caption(f"마감: {row['접수마감일']}")
                                if '공고보기' in row and pd.notna(row['공고보기']):
                                    st.link_button("공고보기", row['공고보기'])
                            
                            with col4:
                                # 개별 확인 버튼
                                button_key = f"confirm_{company['id']}_{idx}_{announcement_name}"
                                if st.button("✅ 확인", key=button_key, type="secondary", use_container_width=True):
                                    # 현재 확인된 공고 목록에 추가
                                    current_seen = st.session_state.get('individual_seen_announcements', [])
                                    if announcement_name not in current_seen:
                                        current_seen.append(announcement_name)
                                        st.session_state['individual_seen_announcements'] = current_seen
                                    
                                    # 개별 공고 확인 상태 저장
                                    st.session_state[announcement_key] = True
                                    
                                    # 데이터베이스에 저장
                                    if save_notifications(company['id'], current_seen):
                                        st.success(f"✅ '{announcement_name}' 확인 처리되었습니다!")
                                        st.rerun()
                                    else:
                                        st.error("❌ 확인 처리에 실패했습니다.")
                            
                            st.divider()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                            
            else:
                # 신규 공고가 없는 경우
                if last_seen_names:
                    # 확인 처리된 공고가 있는 경우
                    st.info(f"✅ 모든 공고를 확인 처리했습니다! (총 {len(last_seen_names)}개 공고 확인됨)")
                    
                    # 확인된 공고 목록을 접을 수 있는 형태로 표시
                    with st.expander("📋 확인된 공고 목록 보기", expanded=False):
                        for i, name in enumerate(last_seen_names, 1):
                            st.write(f"{i}. {name}")
                    
                    # 새로고침 버튼
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("🔄 새로고침", use_container_width=True):
                            st.session_state['notifications_processed'] = False
                            st.rerun()
                else:
                    # 아예 공고가 없는 경우
                    st.info("신규 공고가 없습니다.")
        else:
            st.info("해당 회사의 활성 추천이 없습니다.")
    else:
        st.info("활성 추천 데이터가 없습니다.")

def render_roadmap_tab():
    """12개월 로드맵 탭 렌더링 (recommendations3 테이블 사용)"""
    if 'selected_company' not in st.session_state:
        st.info("사이드바에서 회사를 선택해주세요.")
        return
    
    company = st.session_state['selected_company']
    display_name = company.get('company_name', company.get('name', 'Unknown'))
    st.subheader(f"🗓️ {display_name} 12개월 로드맵")
    
    # 추천 데이터 로드 (recommend3 테이블 사용)
    recommendations2_df = load_recommendations2(company['id'])
    
    # 중복 제거: 공고명별로 가장 높은 총점수를 가진 레코드만 유지
    if not recommendations2_df.empty and '공고제목' in recommendations2_df.columns and '총점수' in recommendations2_df.columns:
        recommendations2_df = recommendations2_df.sort_values('총점수', ascending=False).drop_duplicates(subset=['공고제목'], keep='first')
        recommendations2_df = recommendations2_df.sort_values('총점수', ascending=False)
    
    if not recommendations2_df.empty:
        # 접수시작일 컬럼 확인
        if '접수시작일' not in recommendations2_df.columns:
            st.error("접수시작일 컬럼을 찾을 수 없습니다.")
            return
        
        # 접수시작일에서 월을 추출하는 함수 - 최적화된 버전
        @st.cache_data
        def extract_month_from_date(date_str):
            """접수시작일에서 월을 추출하는 함수 - 캐싱 적용"""
            if pd.isna(date_str) or date_str == '' or str(date_str).strip() == '':
                return None
            
            date_str = str(date_str).strip()
            
            # YYYY-MM-DD 형식인 경우 (가장 일반적) - 최적화
            if len(date_str) == 10 and date_str.count('-') == 2:
                try:
                    return int(date_str.split('-')[1])  # 월 부분만 추출
                except:
                    pass
            
            # N월 형식인 경우 (예: "3월", "12월")
            if '월' in date_str:
                try:
                    month_str = date_str.replace('월', '').strip()
                    month_num = int(month_str)
                    if 1 <= month_num <= 12:
                        return month_num
                except:
                    pass
            
            # MM 형식인 경우 (예: "03", "12")
            try:
                month_num = int(date_str)
                if 1 <= month_num <= 12:
                    return month_num
            except:
                pass
            
            return None
        
        # 접수시작일에서 월 추출
        recommendations2_df['접수월'] = recommendations2_df['접수시작일'].apply(extract_month_from_date)
        
        # 월별 데이터 준비
        monthly_data = []
        monthly_matches = {}  # DataFrame을 별도로 저장
        
        for month in range(1, 13):
            # 접수월이 해당 월과 일치하는 공고 필터링
            month_matches = recommendations2_df[
                recommendations2_df['접수월'] == month
            ]
            
            monthly_data.append({
                'Month': f"{month}월",
                'Count': len(month_matches)
            })
            
            # DataFrame을 별도 딕셔너리에 저장
            monthly_matches[month] = month_matches
        
        # 월별 차트 표시
        chart_data = pd.DataFrame(monthly_data)
        if not chart_data.empty:
            # 공고 수 차트만 표시
            chart_count = alt.Chart(chart_data).mark_bar(color='lightblue').encode(
                x=alt.X('Month:O', sort=['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월']),
                y='Count:Q',
                tooltip=['Month', 'Count']
            ).properties(
                title="월별 공고 수",
                width=600,
                height=300
            )
            st.altair_chart(chart_count)
        
        # 월별 상세 정보
        for month_data in monthly_data:
            month_num = int(month_data['Month'].replace('월', ''))
            month_matches_df = monthly_matches.get(month_num, pd.DataFrame())
            
            # 월별 요약 정보 표시
            if month_data['Count'] > 0:
                st.success(f"📅 {month_data['Month']}: {month_data['Count']}개 공고")
            else:
                st.info(f"📅 {month_data['Month']}: 추천 공고 없음")
            
            with st.expander(f"{month_data['Month']} 상세 정보 ({month_data['Count']}개 공고)"):
                if not month_matches_df.empty:
                    # 추천순위로 정렬 (있는 경우)
                    if '추천순위' in month_matches_df.columns:
                        month_matches_df = month_matches_df.sort_values('추천순위')
                    elif '총점수' in month_matches_df.columns:
                        month_matches_df = month_matches_df.sort_values('총점수', ascending=False)
                    
                    # 표시할 컬럼들 정의
                    display_columns = ['총점수', '적합도', '공고제목', '공고보기', '접수시작일', '접수마감일', '지역', '기관명', '매칭이유']
                    
                    available_columns = [col for col in display_columns if col in month_matches_df.columns]
                    
                    # 데이터 타입 정리
                    display_df = month_matches_df[available_columns].copy()
                    for col in display_df.columns:
                        try:
                            if display_df[col].dtype == 'object':
                                display_df[col] = display_df[col].astype(str)
                        except:
                            # dtype 접근에 실패하면 문자열로 변환
                            display_df[col] = display_df[col].astype(str)
                    
                    # 컬럼 설정
                    column_config = {
                        "매칭이유": st.column_config.TextColumn("매칭 이유", width="large"),
                        "공고제목": st.column_config.TextColumn("공고명", width="large"),
                        "공고보기": st.column_config.LinkColumn("공고보기", width="medium", display_text="공고 보기"),
                        "접수시작일": st.column_config.DateColumn("접수시작일", width="small"),
                        "접수마감일": st.column_config.DateColumn("접수마감일", width="small"),
                        "지역": st.column_config.TextColumn("지역", width="small"),
                        "기관명": st.column_config.TextColumn("기관명", width="medium"),
                        "총점수": st.column_config.NumberColumn("점수", format="%.0f", width="small"),
                        "적합도": st.column_config.TextColumn("적합도", width="small")
                    }
                    
                    st.dataframe(
                        display_df,
                        width='stretch',
                        column_config=column_config
                    )
                    
                    # 월별 통계 정보
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("공고 수", month_data['Count'])
                    with col2:
                        if '총점수' in month_matches_df.columns:
                            avg_score = month_matches_df['총점수'].mean()
                            st.metric("평균 점수", f"{avg_score:.1f}")
                else:
                    st.info("이 달에는 추천 공고가 없습니다. 탐색/서류준비/인증취득 등의 활동을 고려해보세요.")
        
        # CSV 다운로드
        csv = recommendations2_df.to_csv(index=False, encoding='utf-8-sig')
        download_name = company.get('company_name', company.get('name', 'Unknown'))
        st.download_button(
            label="로드맵 데이터 다운로드 (CSV)",
            data=csv,
            file_name=f"{download_name}_roadmap_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("추천 데이터가 없습니다.")

def render_recommendations2_tab():
    """추천 데이터 탭 렌더링 (recommendations3 테이블)"""
    if 'selected_company' not in st.session_state:
        st.info("사이드바에서 회사를 선택해주세요.")
        return
    
    company = st.session_state['selected_company']
    display_name = company.get('company_name', company.get('name', 'Unknown'))
    st.subheader(f"📊 {display_name} 추천 데이터")
    
    # 탭 선택
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["전체 추천", "활성 공고만", "추천(지역)", "추천(키워드)", "추천(규칙)", "추천(3대장)", "필터 옵션"])
    
    with tab1:
        # 전체 추천 (recommendations3 테이블만 사용)
        recommendations2_df = load_recommendations2(company['id'])
        
        if not recommendations2_df.empty:
            # 투자금액을 지원금액으로 컬럼명 변경
            if '투자금액' in recommendations2_df.columns:
                recommendations2_df = recommendations2_df.rename(columns={'투자금액': '지원금액'})
            
            # 중복 제거: 공고명별로 가장 높은 총점수를 가진 레코드만 유지
            if '공고제목' in recommendations2_df.columns and '총점수' in recommendations2_df.columns:
                recommendations2_df = recommendations2_df.sort_values('총점수', ascending=False).drop_duplicates(subset=['공고제목'], keep='first')
                recommendations2_df = recommendations2_df.sort_values('총점수', ascending=False)
            
            st.info(f"📊 총 {len(recommendations2_df)}개의 추천 공고 (recommend3 테이블, 중복 제거)")
            
            # 컬럼명을 한글로 매핑 (공고보기 링크 추가, 순서 조정)
            display_columns = ['총점수', '적합도', '공고제목', '지원가능여부', '공고보기', '접수시작일', '접수마감일', '공고출처', '매칭이유', '공고상세정보']
            available_columns = [col for col in display_columns if col in recommendations2_df.columns]
            
            # 데이터 타입 정리
            display_df = recommendations2_df[available_columns].copy()
            for col in display_df.columns:
                try:
                    if display_df[col].dtype == 'object':
                        display_df[col] = display_df[col].astype(str)
                except:
                    # dtype 접근에 실패하면 문자열로 변환
                    display_df[col] = display_df[col].astype(str)
            
            # 추천순위로 정렬
            if '추천순위' in display_df.columns:
                display_df = display_df.sort_values('추천순위')
            
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "매칭이유": st.column_config.TextColumn("매칭 이유", width="large"),
                    "공고제목": st.column_config.TextColumn("공고명", width="large"),
                    "지원가능여부": st.column_config.TextColumn("지원가능여부", width="small"),
                    "공고보기": st.column_config.LinkColumn("공고보기", width="medium", display_text="공고 보기"),
                    "접수시작일": st.column_config.DateColumn("접수시작일", width="small"),
                    "접수마감일": st.column_config.DateColumn("접수마감일", width="small"),
                    "공고출처": st.column_config.TextColumn("공고출처", width="small"),
                    "공고상세정보": st.column_config.TextColumn("공고상세정보", width="large"),
                    "총점수": st.column_config.NumberColumn("점수", format="%.0f", width="small"),
                    "적합도": st.column_config.TextColumn("적합도", width="small")
                }
            )
        else:
            st.info("해당 회사의 추천 결과가 없습니다.")
    
    with tab2:
        # 활성 공고만 (recommend_active3 테이블 사용)
        active_recommendations_df = load_recommendations3_active(company['id'])
        if not active_recommendations_df.empty:
            # 중복 제거: 공고명별로 가장 높은 총점수를 가진 레코드만 유지
            if '공고제목' in active_recommendations_df.columns and '총점수' in active_recommendations_df.columns:
                active_recommendations_df = active_recommendations_df.sort_values('총점수', ascending=False).drop_duplicates(subset=['공고제목'], keep='first')
                active_recommendations_df = active_recommendations_df.sort_values('총점수', ascending=False)
            
            st.success(f"🟢 {len(active_recommendations_df)}개의 활성 공고가 있습니다! (recommend_active3 테이블, 중복 제거)")
            
            display_columns = ['총점수', '적합도', '공고제목', '지원가능여부', '공고보기', '접수시작일', '접수마감일', '지역', '기관명', '매칭이유']
            available_columns = [col for col in display_columns if col in active_recommendations_df.columns]
            
            # 데이터 타입 정리
            display_df = active_recommendations_df[available_columns].copy()
            for col in display_df.columns:
                try:
                    if display_df[col].dtype == 'object':
                        display_df[col] = display_df[col].astype(str)
                except:
                    # dtype 접근에 실패하면 문자열로 변환
                    display_df[col] = display_df[col].astype(str)
            
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "매칭이유": st.column_config.TextColumn("매칭 이유", width="large"),
                    "공고제목": st.column_config.TextColumn("공고명", width="large"),
                    "지원가능여부": st.column_config.TextColumn("지원가능여부", width="small"),
                    "공고보기": st.column_config.LinkColumn("공고보기", width="medium", display_text="공고 보기"),
                    "접수시작일": st.column_config.DateColumn("접수시작일", width="small"),
                    "접수마감일": st.column_config.DateColumn("접수마감일", width="small"),
                    "공고출처": st.column_config.TextColumn("공고출처", width="small"),
                    "공고상세정보": st.column_config.TextColumn("공고상세정보", width="large"),
                    "총점수": st.column_config.NumberColumn("점수", format="%.0f", width="small"),
                    "적합도": st.column_config.TextColumn("적합도", width="small")
                }
            )
        else:
            st.info("활성 추천 데이터가 없습니다.")
    
    with tab3:
        # 추천(지역) 탭 (recommend_region4 테이블 사용)
        region_recommendations_df = load_recommendations_region4(company['id'])
        
        if not region_recommendations_df.empty:
            # 총점수로 정렬
            if '총점수' in region_recommendations_df.columns:
                region_recommendations_df = region_recommendations_df.sort_values('총점수', ascending=False)
            
            st.success(f"🗺️ {len(region_recommendations_df)}개의 지역별 추천이 있습니다! (recommend_region4 테이블)")
            
            # 지역별 통계 표시
            if '회사지역' in region_recommendations_df.columns:
                region_stats = region_recommendations_df['회사지역'].value_counts()
                st.write("**지역별 추천 현황:**")
                col1, col2, col3 = st.columns(3)
                for i, (region, count) in enumerate(region_stats.items()):
                    if i < 3:
                        with [col1, col2, col3][i]:
                            st.metric(f"{region}", f"{count}개")
            
            # 지역 매칭 여부 표시
            if '지역매칭' in region_recommendations_df.columns:
                region_match_count = region_recommendations_df['지역매칭'].sum() if region_recommendations_df['지역매칭'].dtype == bool else len(region_recommendations_df[region_recommendations_df['지역매칭'] == True])
                total_count = len(region_recommendations_df)
                st.metric("지역 매칭률", f"{region_match_count}/{total_count} ({region_match_count/total_count*100:.1f}%)")
            
            # 표시할 컬럼들 정의 (지역 관련 컬럼 우선, 시기점수와 주요업종 제외)
            display_columns = [
                '총점수', '총점수(10점만점)', '적합도', '공고제목', '회사지역', '프로그램지역', 
                '지역매칭', '지원가능여부', '공고보기', '접수시작일', '접수마감일', 
                '공고출처', '업종점수', '지역점수', '유사도'
            ]
            available_columns = [col for col in display_columns if col in region_recommendations_df.columns]
            
            # 데이터 타입 정리
            display_df = region_recommendations_df[available_columns].copy()
            
            # 중복 컬럼 제거
            display_df = display_df.loc[:, ~display_df.columns.duplicated()]
            for col in display_df.columns:
                try:
                    if display_df[col].dtype == 'object':
                        display_df[col] = display_df[col].astype(str)
                except:
                    # dtype 접근에 실패하면 문자열로 변환
                    display_df[col] = display_df[col].astype(str)
            
            # 인덱스 리셋 (중복 인덱스 문제 해결)
            display_df = display_df.reset_index(drop=True)
            
            # 깔끔한 데이터프레임 표시 (색상 하이라이팅 제거)
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "공고제목": st.column_config.TextColumn("공고명", width="large"),
                    "회사지역": st.column_config.TextColumn("회사지역", width="small"),
                    "프로그램지역": st.column_config.TextColumn("프로그램지역", width="small"),
                    "지역매칭": st.column_config.TextColumn("지역매칭", width="small"),
                    "지원가능여부": st.column_config.TextColumn("지원가능여부", width="small"),
                    "공고보기": st.column_config.LinkColumn("공고보기", width="medium", display_text="공고 보기"),
                    "접수시작일": st.column_config.DateColumn("접수시작일", width="small"),
                    "접수마감일": st.column_config.DateColumn("접수마감일", width="small"),
                    "공고출처": st.column_config.TextColumn("공고출처", width="small"),
                    "업종점수": st.column_config.NumberColumn("업종점수", format="%.1f", width="small"),
                    "지역점수": st.column_config.NumberColumn("지역점수", format="%.0f", width="small"),
                    "유사도": st.column_config.NumberColumn("유사도", format="%.3f", width="small"),
                    "총점수": st.column_config.NumberColumn("총점수", format="%.1f", width="small"),
                    "총점수(10점만점)": st.column_config.NumberColumn("총점수(10점만점)", format="%.1f", width="small"),
                    "적합도": st.column_config.TextColumn("적합도", width="small")
                }
            )
            
            # CSV 다운로드
            csv = region_recommendations_df.to_csv(index=False, encoding='utf-8-sig')
            download_name = company.get('company_name', company.get('name', 'Unknown'))
            st.download_button(
                label="지역별 추천 데이터 다운로드 (CSV)",
                data=csv,
                file_name=f"{download_name}_region_recommendations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("지역별 추천 데이터가 없습니다.")
    
    with tab4:
        # 추천(키워드) 탭 (recommend_keyword4 테이블 사용)
        keyword_recommendations_df = load_recommendations_keyword4(company['id'])
        
        if not keyword_recommendations_df.empty:
            # 키워드점수로 정렬
            if '키워드점수' in keyword_recommendations_df.columns:
                keyword_recommendations_df = keyword_recommendations_df.sort_values('키워드점수', ascending=False)
            
            st.success(f"🔑 {len(keyword_recommendations_df)}개의 키워드별 추천이 있습니다! (recommend_keyword4 테이블)")
            
            # 키워드 점수 통계 표시
            if '키워드점수' in keyword_recommendations_df.columns:
                avg_keyword_score = keyword_recommendations_df['키워드점수'].mean()
                max_keyword_score = keyword_recommendations_df['키워드점수'].max()
                st.metric("평균 키워드 점수", f"{avg_keyword_score:.2f}")
                st.metric("최고 키워드 점수", f"{max_keyword_score:.2f}")
            
            # 표시할 컬럼들 정의 (키워드 관련 컬럼 우선, 일부 컬럼 제외)
            display_columns = [
                '키워드점수', '공고제목', '회사명', '공고보기', '접수시작일', '접수마감일', 
                '키워드교집합', '프로그램ID'
            ]
            available_columns = [col for col in display_columns if col in keyword_recommendations_df.columns]
            
            # 데이터 타입 정리
            display_df = keyword_recommendations_df[available_columns].copy()
            
            # 중복 컬럼 제거
            display_df = display_df.loc[:, ~display_df.columns.duplicated()]
            for col in display_df.columns:
                try:
                    if str(display_df[col].dtype) == 'object':
                        display_df[col] = display_df[col].astype(str)
                except:
                    # dtype 접근에 실패하면 문자열로 변환
                    display_df[col] = display_df[col].astype(str)
            
            # 인덱스 리셋 (중복 인덱스 문제 해결)
            display_df = display_df.reset_index(drop=True)
            
            # 깔끔한 데이터프레임 표시
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "공고제목": st.column_config.TextColumn("공고명", width="large"),
                    "회사명": st.column_config.TextColumn("회사명", width="small"),
                    "공고보기": st.column_config.LinkColumn("공고보기", width="medium", display_text="공고 보기"),
                    "접수시작일": st.column_config.DateColumn("접수시작일", width="small"),
                    "접수마감일": st.column_config.DateColumn("접수마감일", width="small"),
                    "키워드점수": st.column_config.NumberColumn("키워드점수", format="%.2f", width="small"),
                    "키워드교집합": st.column_config.TextColumn("키워드교집합", width="medium"),
                    "프로그램ID": st.column_config.TextColumn("프로그램ID", width="small")
                }
            )
            
            # CSV 다운로드
            csv = keyword_recommendations_df.to_csv(index=False, encoding='utf-8-sig')
            download_name = company.get('company_name', company.get('name', 'Unknown'))
            st.download_button(
                label="키워드별 추천 데이터 다운로드 (CSV)",
                data=csv,
                file_name=f"{download_name}_keyword_recommendations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("키워드별 추천 데이터가 없습니다.")
    
    with tab5:
        # 추천(규칙) 탭 (recommend_rules4 테이블 사용)
        rules_recommendations_df = load_recommendations_rules4(company['id'])
        
        if not rules_recommendations_df.empty:
            # 통과여부로 정렬
            if '통과여부' in rules_recommendations_df.columns:
                rules_recommendations_df = rules_recommendations_df.sort_values('통과여부', ascending=False)
            
            st.success(f"📋 {len(rules_recommendations_df)}개의 규칙별 추천이 있습니다! (recommend_rules4 테이블)")
            
            # 통과 통계 표시
            if '통과여부' in rules_recommendations_df.columns:
                passed_count = rules_recommendations_df['통과여부'].sum() if rules_recommendations_df['통과여부'].dtype == bool else len(rules_recommendations_df[rules_recommendations_df['통과여부'] == True])
                total_count = len(rules_recommendations_df)
                st.metric("규칙 통과율", f"{passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
            
            # 표시할 컬럼들 정의 (규칙 관련 컬럼 우선)
            display_columns = [
                '통과여부', '공고제목', '회사명', '공고보기', '접수시작일', '접수마감일', 
                '통과이유', '회사지역', '프로그램지역', '회사업력', '최소업력', '최대업력',
                '회사업종', '프로그램업종', '우선순위유형', '프로그램ID'
            ]
            available_columns = [col for col in display_columns if col in rules_recommendations_df.columns]
            
            # 데이터 타입 정리
            display_df = rules_recommendations_df[available_columns].copy()
            
            # 중복 컬럼 제거
            display_df = display_df.loc[:, ~display_df.columns.duplicated()]
            for col in display_df.columns:
                try:
                    if str(display_df[col].dtype) == 'object':
                        display_df[col] = display_df[col].astype(str)
                except:
                    # dtype 접근에 실패하면 문자열로 변환
                    display_df[col] = display_df[col].astype(str)
            
            # 인덱스 리셋 (중복 인덱스 문제 해결)
            display_df = display_df.reset_index(drop=True)
            
            # 깔끔한 데이터프레임 표시
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "공고제목": st.column_config.TextColumn("공고명", width="large"),
                    "회사명": st.column_config.TextColumn("회사명", width="small"),
                    "공고보기": st.column_config.LinkColumn("공고보기", width="medium", display_text="공고 보기"),
                    "접수시작일": st.column_config.DateColumn("접수시작일", width="small"),
                    "접수마감일": st.column_config.DateColumn("접수마감일", width="small"),
                    "통과여부": st.column_config.TextColumn("통과여부", width="small"),
                    "통과이유": st.column_config.TextColumn("통과이유", width="large"),
                    "회사지역": st.column_config.TextColumn("회사지역", width="small"),
                    "프로그램지역": st.column_config.TextColumn("프로그램지역", width="small"),
                    "회사업력": st.column_config.NumberColumn("회사업력", format="%.0f", width="small"),
                    "최소업력": st.column_config.NumberColumn("최소업력", format="%.0f", width="small"),
                    "최대업력": st.column_config.NumberColumn("최대업력", format="%.0f", width="small"),
                    "회사업종": st.column_config.TextColumn("회사업종", width="medium"),
                    "프로그램업종": st.column_config.TextColumn("프로그램업종", width="medium"),
                    "우선순위유형": st.column_config.TextColumn("우선순위유형", width="small"),
                    "프로그램ID": st.column_config.TextColumn("프로그램ID", width="small")
                }
            )
            
            # CSV 다운로드
            csv = rules_recommendations_df.to_csv(index=False, encoding='utf-8-sig')
            download_name = company.get('company_name', company.get('name', 'Unknown'))
            st.download_button(
                label="규칙별 추천 데이터 다운로드 (CSV)",
                data=csv,
                file_name=f"{download_name}_rules_recommendations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("규칙별 추천 데이터가 없습니다.")
    
    with tab6:
        # 추천(3대장) 탭 (recommend_priority4 테이블 사용)
        priority_recommendations_df = load_recommendations_priority4(company['id'])
        
        if not priority_recommendations_df.empty:
            # 총점수로 정렬
            if '총점수' in priority_recommendations_df.columns:
                priority_recommendations_df = priority_recommendations_df.sort_values('총점수', ascending=False)
            
            st.success(f"🏆 {len(priority_recommendations_df)}개의 3대장별 추천이 있습니다! (recommend_priority4 테이블)")
            
            # 3대장 점수 통계 표시
            if '총점수' in priority_recommendations_df.columns:
                avg_score = priority_recommendations_df['총점수'].mean()
                max_score = priority_recommendations_df['총점수'].max()
                st.metric("평균 총점수", f"{avg_score:.2f}")
                st.metric("최고 총점수", f"{max_score:.2f}")
            
            # 우선순위 유형별 통계
            if '우선순위유형' in priority_recommendations_df.columns:
                priority_stats = priority_recommendations_df['우선순위유형'].value_counts()
                st.write("**우선순위 유형별 현황:**")
                col1, col2, col3 = st.columns(3)
                for i, (priority_type, count) in enumerate(priority_stats.items()):
                    if i < 3:
                        with [col1, col2, col3][i]:
                            st.metric(f"{priority_type}", f"{count}개")
            
            # 표시할 컬럼들 정의 (3대장 관련 컬럼 우선, 시기점수와 주요업종 제외)
            display_columns = [
                '총점수', '총점수(10점만점)', '공고제목', '우선순위유형', '적합도', '회사명', '공고보기', '접수시작일', '접수마감일', 
                '공고출처', '업종점수', '지역점수', '유사도', '프로그램ID', '지원가능여부'
            ]
            available_columns = [col for col in display_columns if col in priority_recommendations_df.columns]
            
            # 데이터 타입 정리
            display_df = priority_recommendations_df[available_columns].copy()
            
            # 중복 컬럼 제거
            display_df = display_df.loc[:, ~display_df.columns.duplicated()]
            for col in display_df.columns:
                try:
                    if str(display_df[col].dtype) == 'object':
                        display_df[col] = display_df[col].astype(str)
                except:
                    # dtype 접근에 실패하면 문자열로 변환
                    display_df[col] = display_df[col].astype(str)
            
            # 인덱스 리셋 (중복 인덱스 문제 해결)
            display_df = display_df.reset_index(drop=True)
            
            # 깔끔한 데이터프레임 표시
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "공고제목": st.column_config.TextColumn("공고명", width="large"),
                    "회사명": st.column_config.TextColumn("회사명", width="small"),
                    "공고보기": st.column_config.LinkColumn("공고보기", width="medium", display_text="공고 보기"),
                    "접수시작일": st.column_config.DateColumn("접수시작일", width="small"),
                    "접수마감일": st.column_config.DateColumn("접수마감일", width="small"),
                    "공고출처": st.column_config.TextColumn("공고출처", width="small"),
                    "업종점수": st.column_config.NumberColumn("업종점수", format="%.1f", width="small"),
                    "지역점수": st.column_config.NumberColumn("지역점수", format="%.0f", width="small"),
                    "유사도": st.column_config.NumberColumn("유사도", format="%.3f", width="small"),
                    "우선순위유형": st.column_config.TextColumn("우선순위유형", width="small"),
                    "프로그램ID": st.column_config.TextColumn("프로그램ID", width="small"),
                    "지원가능여부": st.column_config.TextColumn("지원가능여부", width="small"),
                    "총점수": st.column_config.NumberColumn("총점수", format="%.1f", width="small"),
                    "총점수(10점만점)": st.column_config.NumberColumn("총점수(10점만점)", format="%.1f", width="small"),
                    "적합도": st.column_config.TextColumn("적합도", width="small")
                }
            )
            
            # CSV 다운로드
            csv = priority_recommendations_df.to_csv(index=False, encoding='utf-8-sig')
            download_name = company.get('company_name', company.get('name', 'Unknown'))
            st.download_button(
                label="3대장별 추천 데이터 다운로드 (CSV)",
                data=csv,
                file_name=f"{download_name}_priority_recommendations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("3대장별 추천 데이터가 없습니다.")
    
    with tab7:
        # 필터 옵션 탭
        st.subheader("🔍 필터 옵션")
        
        # 전체 추천 데이터 로드
        recommendations2_df = load_recommendations2(company['id'])
        
        if not recommendations2_df.empty:
            # 상태별 필터링 옵션 (간단하게)
            st.write("**상태별 필터링**")
            col1, col2 = st.columns(2)
            
            with col1:
                show_approved = st.checkbox("승인된 공고", value=False, key="filter_approved")
            with col2:
                show_rejected = st.checkbox("반려된 공고", value=False, key="filter_rejected")
            
            # 필터 적용
            filtered_df = recommendations2_df.copy()
            
            # 상태별 필터링 (세션 상태 기반)
            if show_approved or show_rejected:
                # 세션 상태에서 필터링
                company_name = company.get('company_name', company.get('name', ''))
                filtered_rows = []
                
                for idx, row in filtered_df.iterrows():
                    current_status = get_recommendation_status(company_name, row['공고제목'])
                    
                    if show_approved and current_status == 'approved':
                        filtered_rows.append(idx)
                    elif show_rejected and current_status == 'rejected':
                        filtered_rows.append(idx)
                
                if filtered_rows:
                    filtered_df = filtered_df.loc[filtered_rows]
                else:
                    filtered_df = pd.DataFrame()  # 빈 결과
            else:
                # 아무것도 선택하지 않으면 모든 공고 표시
                pass
            
            # 결과 표시
            st.write(f"**필터링 결과: {len(filtered_df)}개 공고**")
            
            if not filtered_df.empty:
                # 각 공고에 대해 승인/반려 버튼과 함께 표시
                for i, (idx, row) in enumerate(filtered_df.iterrows()):
                    with st.container():
                        # 세션 상태에서 현재 상태 확인
                        company_name = company.get('company_name', company.get('name', ''))
                        current_status = get_recommendation_status(company_name, row['공고제목'])
                        
                        # 상태에 따른 색깔 표시
                        if current_status == 'approved':
                            st.success(f"✅ 승인됨: {row['공고제목']}")
                        elif current_status == 'rejected':
                            st.error(f"❌ 반려됨: {row['공고제목']}")
                        else:
                            st.info(f"⏳ 대기중: {row['공고제목']}")
                        
                        # 공고 정보 표시
                        col1, col2, col3 = st.columns([6, 1, 1])
                        
                        with col1:
                            st.write(f"**공고명**: {row['공고제목']}")
                            st.write(f"**접수기간**: {row.get('접수시작일', 'N/A')} ~ {row.get('접수마감일', 'N/A')}")
                            st.write(f"**총점수**: {row.get('총점수', 'N/A')}")
                            st.write(f"**매칭이유**: {row.get('매칭이유', 'N/A')}")
                            if '공고보기' in row and pd.notna(row['공고보기']):
                                st.write(f"**공고보기**: [링크]({row['공고보기']})")
                        
                        with col2:
                            if current_status == 'approved':
                                if st.button("✅ 승인됨", key=f"approve_{i}", type="primary"):
                                    if update_recommendation_status(company_name, row['공고제목'], 'pending'):
                                        st.rerun()
                            else:
                                if st.button("승인", key=f"approve_{i}", type="primary"):
                                    if update_recommendation_status(company_name, row['공고제목'], 'approved'):
                                        st.rerun()
                        
                        with col3:
                            if current_status == 'rejected':
                                if st.button("❌ 반려됨", key=f"reject_{i}", type="secondary"):
                                    if update_recommendation_status(company_name, row['공고제목'], 'pending'):
                                        st.rerun()
                            else:
                                if st.button("반려", key=f"reject_{i}", type="secondary"):
                                    if update_recommendation_status(company_name, row['공고제목'], 'rejected'):
                                        st.rerun()
                        
                        st.divider()
            else:
                st.info("필터 조건에 맞는 공고가 없습니다.")
        else:
            st.info("추천 데이터가 없습니다.")

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
            # 기업명이 있으면 기업명 표시, 없으면 전체 이름 표시
            display_name = company.get('company_name', company.get('name', 'Unknown'))
            st.subheader(f"🏢 {display_name}")
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
        tab1, tab2, tab3 = st.tabs(["📊 추천 데이터", "🔔 신규 공고 알림", "🗓️ 12개월 로드맵"])
        
        with tab1:
            render_recommendations2_tab()
        
        with tab2:
            render_alerts_tab()
        
        with tab3:
            render_roadmap_tab()
    else:
        st.info("👈 사이드바에서 회사를 선택해주세요.")

if __name__ == "__main__":
    main()
