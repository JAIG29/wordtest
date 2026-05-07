# "https://docs.google.com/spreadsheets/d/e/2PACX-1vS_iSSqHOEkErKFox3ynYjV9xVuIn4eEehgcJIRW3NBxxkrxA9e27tg20Xu_SzLVCFb0V0gHcBZpLPc/pub?output=csv"

import streamlit as st  # Streamlit 프레임워크 임포트
import pandas as pd  # 데이터 분석을 위한 Pandas 임포트
import random  # 무작위 선택을 위한 random 임포트
import time  # 시간 지연을 위한 time 임포트
import streamlit.components.v1 as components  # 자바스크립트 실행을 위한 컴포넌트 임포트

# --- 설정 (구글 시트 웹 게시 CSV 주소를 입력하세요) ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS_iSSqHOEkErKFox3ynYjV9xVuIn4eEehgcJIRW3NBxxkrxA9e27tg20Xu_SzLVCFb0V0gHcBZpLPc/pub?output=csv"

# 페이지 기본 설정 (타이틀, 레이아웃)
st.set_page_config(page_title="스마트 단어 퀴즈", layout="centered")

# --- 1. CSS 적용 (폰트 적용 및 크기 조정) ---
# Pretendard 웹 폰트를 불러오고 모든 요소에 강제 적용합니다.
st.markdown("""
    <style>
    /* Pretendard 폰트 불러오기 (CDN) */
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");
    
    /* 전체 요소에 폰트 적용 및 기본 설정 */
    html, body, [class*="st-"], div, span, p, button {
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, "Helvetica Neue", "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", sans-serif !important;
    }
    
    /* 상단 타이틀 폰트 크기 축소 */
    .st-emotion-cache-10trblm { 
        font-size: 24px !important; 
    }
    h1 { 
        font-size: 1.5rem !important; 
        font-weight: 700 !important;
        color: #444;
    }
    
    /* 메인 단어(문제) 폰트 크기 대폭 확대 */
    .main-word {
        font-size: 3.5rem !important; /* 단어 크기를 키움 */
        font-weight: 800;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 30px;
        color: #000;
        word-break: keep-all;
    }
    
    /* 선택지 버튼 스타일 조정 */
    .stButton>button {
        font-size: 1.2rem !important;
        padding: 10px 20px !important;
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. TTS(음성 합성) 기능 함수 ---
def speak_word(word):
    # 브라우저 내부 API를 사용하여 영문 단어를 읽어주는 자바스크립트 생성
    js_code = f"""
    <script>
    var msg = new SpeechSynthesisUtterance('{word}');
    msg.lang = 'en-US'; // 언어 설정
    msg.rate = 1.0;    // 속도 설정
    window.speechSynthesis.speak(msg);
    </script>
    """
    # 자바스크립트를 화면에 삽입하여 실행 (높이 0으로 보이지 않게 처리)
    components.html(js_code, height=0)

# --- 3. 데이터 불러오기 함수 ---
@st.cache_data(ttl=60) # 60초 동안 캐싱하여 반복 로딩 방지
def load_data():
    try:
        # 구글 시트 CSV URL 읽기
        df = pd.read_csv(SHEET_CSV_URL)
        # 열 이름을 단어와 뜻으로 지정
        df.columns = ['word', 'meaning']
        # 빈 줄 제거 후 리스트 형식으로 반환
        return df.dropna().to_dict('records')
    except:
        # 오류 발생 시 빈 리스트 반환
        return []

# 데이터 로드 실행
data = load_data()

# --- 4. 메인 앱 화면 구성 ---
st.title("🎧 스마트 단어 학습") # 상단 타이틀 (폰트 축소 적용됨)

# 데이터가 충분한지 확인 (5지선다를 위해 최소 5개 필요)
if not data or len(data) < 5:
    st.warning("데이터가 부족합니다. 구글 시트에 단어를 5개 이상 입력해주세요.")
else:
    # 학습 모드 선택 (가로 배열 라디오 버튼)
    mode = st.radio("학습 모드 선택", ["단어 → 뜻", "뜻 → 단어"], horizontal=True)

    # 세션 상태 초기화 (현재 문제, 선택지, 정답 여부 저장)
    if 'quiz' not in st.session_state:
        st.session_state.quiz = None
        st.session_state.options = []
        st.session_state.answered = False

    # 새로운 문제를 생성하는 함수
    def generate_question():
        correct = random.choice(data) # 정답 무작위 선택
        # 정답을 제외한 나머지 데이터에서 오답 4개 추출
        others = random.sample([item for item in data if item != correct], 4)
        options = [correct] + others # 정답과 오답 합치기
        random.shuffle(options) # 선택지 순서 섞기
        
        st.session_state.quiz = correct # 세션에 정답 저장
        st.session_state.options = options # 세션에 선택지 저장
        st.session_state.answered = False # 답변 안함 상태로 초기화

    # 퀴즈 데이터가 없으면 최초 생성
    if st.session_state.quiz is None:
        generate_question()

    # 현재 퀴즈 정보 가져오기
    quiz = st.session_state.quiz
    options = st.session_state.options

    st.divider() # 구분선 추가
    
    # 문제 텍스트 결정 (단어 혹은 뜻)
    display_text = quiz['word'] if mode == "단어 → 뜻" else quiz['meaning']
    # 화면 중앙에 크게 문제 표시 (CSS 클래스 적용)
    st.markdown(f'<p class="main-word">{display_text}</p>', unsafe_allow_html=True)

    # 정답 텍스트와 버튼에 표시할 레이블 결정
    correct_answer = quiz['meaning'] if mode == "단어 → 뜻" else quiz['word']
    option_labels = [opt['meaning'] if mode == "단어 → 뜻" else opt['word'] for opt in options]

    # 5개의 선택지 버튼 생성
    for label in option_labels:
        # 버튼을 클릭했고 아직 답변하지 않은 상태인 경우 실행
        if st.button(label, use_container_width=True, disabled=st.session_state.answered):
            st.session_state.answered = True # 답변 완료 상태로 변경
            speak_word(quiz['word']) # 영어 발음 재생
            
            # 정답 확인 및 결과 메시지 표시
            if label == correct_answer:
                st.success(f"⭕ 정답입니다!")
            else:
                st.error(f"❌ 틀렸습니다! 정답: {correct_answer}")
            
            # 결과 확인을 위해 1.2초 대기 후 자동으로 다음 문제로 이동
            time.sleep(1.2)
            generate_question() # 새로운 문제 생성
            st.rerun() # 앱 화면 새로고침

    st.divider() # 하단 구분선
    # 현재 데이터베이스 정보 표시
    st.caption(f"학습 데이터: {len(data)}개 단어 연결됨")