import streamlit as st # Streamlit 임포트
import pandas as pd # 데이터 처리를 위한 Pandas
import random # 무작위 선택
import time # 자동 넘김 지연 시간
import streamlit.components.v1 as components # TTS 실행용

# --- 설정 (구글 시트 CSV 주소) ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vReAkoC2Ndx4DaeC-eqqGlRUSLMaXo7RCwBqJDj3SFZf4BX2I_9oi2s-E1Xkt_uF4X2G4GMiT8Y9YUw/pub?output=csv"

# 페이지 설정
st.set_page_config(page_title="주하 Word Test", layout="centered")

# --- 1. 모바일 맞춤형 디자인 및 폰트 설정 ---
st.markdown("""
    <style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    html, body, [class*="st-"], div, span, p, button, label, input {
        font-family: "Pretendard", -apple-system, sans-serif !important;
    }

    #MainMenu, footer, header {visibility: hidden;}

    /* 상단 헤더 영역 (제목 + 점수판) */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: -10px;
        margin-bottom: 5px;
    }

    .small-title {
        font-size: 16px !important;
        font-weight: 700;
        color: #888;
    }

    .score-board {
        font-size: 16px !important;
        font-weight: 700;
    }

    .score-correct { color: #28a745; margin-right: 10px; }
    .score-incorrect { color: #dc3545; }

    /* 중앙 단어 */
    .main-word {
        font-size: 3rem !important;
        font-weight: 800;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 20px;
        color: #111;
        line-height: 1.1;
    }

    /* 선택지 버튼 */
    .stButton>button {
        font-size: 1.1rem !important;
        padding: 10px !important;
        margin-bottom: -8px !important;
        border-radius: 12px !important;
        height: 50px !important; 
        background-color: #fcfcfc !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 기능 함수 (TTS, 데이터 로드) ---
def speak_word(word):
    js_code = f"<script>var msg = new SpeechSynthesisUtterance('{word}'); msg.lang = 'en-US'; window.speechSynthesis.speak(msg);</script>"
    components.html(js_code, height=0)

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        df.columns = ['word', 'meaning']
        return df.dropna().to_dict('records')
    except:
        return []

data = load_data()

# --- 3. 세션 상태 초기화 (점수 기록 추가) ---
if 'correct' not in st.session_state:
    st.session_state.correct = 0
if 'incorrect' not in st.session_state:
    st.session_state.incorrect = 0
if 'quiz' not in st.session_state:
    st.session_state.quiz = None
    st.session_state.options = []
    st.session_state.answered = False

# --- 4. 메인 화면 구성 ---
# 상단 제목 및 점수판 레이아웃
st.markdown(f"""
    <div class="header-container">
        <div class="small-title">주하 Word Test</div>
        <div class="score-board">
            <span class="score-correct">⭕ {st.session_state.correct}</span>
            <span class="score-incorrect">❌ {st.session_state.incorrect}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

if not data or len(data) < 5:
    st.warning("단어를 5개 이상 입력해주세요.")
else:
    mode = st.radio("", ["단어→뜻", "뜻→단어"], horizontal=True)

    def generate_question():
        correct_item = random.choice(data)
        others = random.sample([item for item in data if item != correct_item], 4)
        options = [correct_item] + others
        random.shuffle(options)
        st.session_state.quiz = correct_item
        st.session_state.options = options
        st.session_state.answered = False

    if st.session_state.quiz is None:
        generate_question()

    quiz = st.session_state.quiz
    options = st.session_state.options

    # 문제 표시
    display_text = quiz['word'] if mode == "단어→뜻" else quiz['meaning']
    st.markdown(f'<p class="main-word">{display_text}</p>', unsafe_allow_html=True)

    correct_answer = quiz['meaning'] if mode == "단어→뜻" else quiz['word']
    option_labels = [opt['meaning'] if mode == "단어→뜻" else opt['word'] for opt in options]

    # 선택지 버튼 및 로직
    for label in option_labels:
        if st.button(label, use_container_width=True, disabled=st.session_state.answered):
            st.session_state.answered = True
            speak_word(quiz['word'])
            
            if label == correct_answer:
                st.session_state.correct += 1 # 맞힌 개수 증가
                st.success("정답입니다!")
            else:
                st.session_state.incorrect += 1 # 틀린 개수 증가
                st.error(f"오답! 정답: {correct_answer}")
            
            time.sleep(1.0)
            generate_question()
            st.rerun()

    st.caption(f"총 단어 수: {len(data)}")