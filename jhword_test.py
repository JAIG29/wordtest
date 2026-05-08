#SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vReAkoC2Ndx4DaeC-eqqGlRUSLMaXo7RCwBqJDj3SFZf4BX2I_9oi2s-E1Xkt_uF4X2G4GMiT8Y9YUw/pub?output=csv"


import streamlit as st
import pandas as pd
import random
import time
import streamlit.components.v1 as components

# --- 설정 (구글 시트 CSV 주소) ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vReAkoC2Ndx4DaeC-eqqGlRUSLMaXo7RCwBqJDj3SFZf4BX2I_9oi2s-E1Xkt_uF4X2G4GMiT8Y9YUw/pub?output=csv"

st.set_page_config(page_title="주하 Word Test", layout="centered")

# --- 1. 모바일 최적화 디자인 (Pretendard & No-Scroll) ---
st.markdown("""
    <style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");
    .block-container { padding: 0.8rem !important; padding-top: 0.5rem !important; }
    html, body, [class*="st-"], div, span, p, button { font-family: "Pretendard", sans-serif !important; }
    #MainMenu, footer, header {visibility: hidden;}

    .status-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
    .title-text { font-size: 15px; font-weight: 700; color: #888; }
    .score-text { font-size: 15px; font-weight: 700; }

    .main-word {
        font-size: 2.8rem !important;
        font-weight: 800;
        text-align: center;
        margin: 10px 0 10px 0;
        color: #111;
        line-height: 1.1;
    }
    .meaning-reveal {
        font-size: 1.8rem !important;
        font-weight: 600;
        text-align: center;
        color: #007bff;
        margin-bottom: 15px;
    }
    .stButton>button {
        font-size: 1.1rem !important;
        padding: 8px !important;
        margin-bottom: -12px !important;
        border-radius: 12px !important;
        height: 46px !important;
    }
    /* O, X 버튼 전용 스타일 */
    .ox-container { display: flex; gap: 10px; margin-top: 10px; }
    .stProgress { height: 4px !important; margin-bottom: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. TTS 함수 (영어 목소리 강제 선택 강화) ---
def play_feedback(word, is_correct=True, buzzer=False):
    buzzer_js = ""
    if buzzer:
        buzzer_js = "var ctx=new(window.AudioContext||window.webkitAudioContext)();var osc=ctx.createOscillator();var gain=ctx.createGain();osc.type='sawtooth';osc.frequency.setValueAtTime(150,ctx.currentTime);gain.gain.setValueAtTime(0.1,ctx.currentTime);osc.connect(gain);gain.connect(ctx.destination);osc.start();osc.stop(ctx.currentTime+0.3);"
    
    # 브라우저에 등록된 목소리 중 영어(en)가 포함된 목소리를 찾아 강제로 할당
    js_code = f"""
    <script>
    {buzzer_js}
    setTimeout(function() {{
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{word}');
        var voices = window.speechSynthesis.getVoices();
        // 영어 목소리 우선 선택 (Google US English 등)
        var enVoice = voices.find(v => v.lang.includes('en') || v.name.includes('English'));
        if(enVoice) msg.voice = enVoice;
        msg.lang = 'en-US';
        window.speechSynthesis.speak(msg);
    }}, {0 if not buzzer else 400});
    </script>
    """
    components.html(js_code, height=0)

# --- 3. 데이터 로드 ---
@st.cache_data(ttl=60)
def load_all_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        df.columns = ['word', 'meaning', 'target']
        full_list = df.dropna(subset=['word', 'meaning']).to_dict('records')
        target_list = [item for item in full_list if str(item['target']).upper() == 'Y']
        return full_list, target_list
    except:
        return [], []

full_data, target_data = load_all_data()

# --- 4. 세션 상태 관리 ---
for key in ['quiz_pool', 'incorrect_bucket', 'current_idx', 'correct_ans', 'is_finished', 'quiz_item', 'options', 'answered', 'show_card_meaning']:
    if key not in st.session_state:
        if key == 'quiz_pool' or key == 'incorrect_bucket' or key == 'options': st.session_state[key] = []
        elif key == 'current_idx' or key == 'correct_ans': st.session_state[key] = 0
        elif key == 'is_finished' or key == 'answered' or key == 'show_card_meaning': st.session_state[key] = False
        else: st.session_state[key] = None

def start_new_round(words):
    random.shuffle(words)
    st.session_state.quiz_pool = words
    st.session_state.incorrect_bucket = []
    st.session_state.current_idx = 0
    st.session_state.correct_ans = 0
    st.session_state.is_finished = False
    st.session_state.quiz_item = None
    st.session_state.show_card_meaning = False

def get_next_question():
    if st.session_state.current_idx < len(st.session_state.quiz_pool):
        correct_item = st.session_state.quiz_pool[st.session_state.current_idx]
        others = random.sample([item for item in full_data if item['word'] != correct_item['word']], min(4, len(full_data)-1))
        options = [correct_item] + others
        random.shuffle(options)
        st.session_state.quiz_item = correct_item
        st.session_state.options = options
        st.session_state.answered = False
        st.session_state.show_card_meaning = False
    else:
        st.session_state.is_finished = True

if not st.session_state.quiz_pool and target_data:
    start_new_round(target_data)

# --- 5. 메인 UI ---
st.markdown(f'<div class="status-bar"><div class="title-text">주하 Word Test</div><div class="score-text"><span style="color:#28a745">⭕ {st.session_state.correct_ans}</span><span style="color:#dc3545; margin-left:8px">❌ {len(st.session_state.incorrect_bucket)}</span></div></div>', unsafe_allow_html=True)

if not target_data:
    st.warning("C열에 'Y'를 입력한 단어가 없습니다.")
else:
    if st.session_state.is_finished:
        st.markdown('<p style="text-align:center; font-size:24px; font-weight:700;">학습 완료!</p>', unsafe_allow_html=True)
        wrong = len(st.session_state.incorrect_bucket)
        if wrong > 0 and st.button(f"❌ 오답 {wrong}개 복습하기", use_container_width=True):
            start_new_round(st.session_state.incorrect_bucket); st.rerun()
        if st.button("🔄 전체 다시 시작", use_container_width=True):
            start_new_round(target_data); st.rerun()
    else:
        if st.session_state.quiz_item is None: get_next_question()

        st.progress(st.session_state.current_idx / len(st.session_state.quiz_pool))
        # 모드 선택 (기본값: 뜻→단어)
        mode = st.radio("", ["뜻→단어", "단어→뜻", "5초 카드"], horizontal=True, label_visibility="collapsed")
        
        quiz = st.session_state.quiz_item
        
        # 5초 카드 학습 모드
        if mode == "5초 카드":
            st.markdown(f'<p class="main-word">{quiz["word"]}</p>', unsafe_allow_html=True)
            placeholder = st.empty()
            
            if not st.session_state.show_card_meaning:
                play_feedback(quiz['word']) # 단어 먼저 읽어주기
                with placeholder.container():
                    st.markdown('<p style="text-align:center; color:#888;">뜻 생각 중... (5초)</p>', unsafe_allow_html=True)
                    time.sleep(5)
                st.session_state.show_card_meaning = True
                st.rerun()
            else:
                placeholder.markdown(f'<p class="meaning-reveal">{quiz["meaning"]}</p>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                if col1.button("⭕ 맞힘", use_container_width=True):
                    st.session_state.correct_ans += 1
                    st.session_state.current_idx += 1
                    get_next_question(); st.rerun()
                if col2.button("❌ 틀림", use_container_width=True):
                    st.session_state.incorrect_bucket.append(quiz)
                    st.session_state.current_idx += 1
                    get_next_question(); st.rerun()

        # 객관식 퀴즈 모드
        else:
            display_text = quiz['word'] if mode == "단어→뜻" else quiz['meaning']
            st.markdown(f'<p class="main-word">{display_text}</p>', unsafe_allow_html=True)
            correct_answer = quiz['meaning'] if mode == "단어→뜻" else quiz['word']
            
            for item in st.session_state.options:
                label = item['meaning'] if mode == "단어→뜻" else item['word']
                if st.button(label, use_container_width=True, disabled=st.session_state.answered):
                    st.session_state.answered = True
                    is_correct = (label == correct_answer)
                    play_feedback(quiz['word'], buzzer=not is_correct)
                    if is_correct: 
                        st.session_state.correct_ans += 1
                        st.success("정답!")
                    else: 
                        st.session_state.incorrect_bucket.append(quiz)
                        st.error(f"정답: {correct_answer}")
                    time.sleep(1.2)
                    st.session_state.current_idx += 1
                    get_next_question(); st.rerun()

        st.caption(f"Progress: {st.session_state.current_idx + 1} / {len(st.session_state.quiz_pool)}")