import streamlit as st
import pandas as pd
import random
import time
import streamlit.components.v1 as components

# --- 설정 (구글 시트 CSV 주소) ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vReAkoC2Ndx4DaeC-eqqGlRUSLMaXo7RCwBqJDj3SFZf4BX2I_9oi2s-E1Xkt_uF4X2G4GMiT8Y9YUw/pub?output=csv"

# 페이지 기본 설정
st.set_page_config(page_title="주하 Word Test", layout="centered")

# --- 1. 모바일 최적화 디자인 및 스타일 ---
st.markdown("""
    <style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");
    .block-container { padding: 0.8rem !important; padding-top: 0.5rem !important; }
    html, body, [class*="st-"], div, span, p, button { font-family: "Pretendard", sans-serif !important; }
    #MainMenu, footer, header {visibility: hidden;}
    .status-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
    .title-text { font-size: 15px; font-weight: 700; color: #888; }
    .score-text { font-size: 15px; font-weight: 700; }
    .main-word { font-size: 2.6rem !important; font-weight: 800; text-align: center; margin: 10px 0; color: #111; line-height: 1.1; }
    .meaning-reveal { font-size: 1.8rem !important; font-weight: 600; text-align: center; color: #007bff; margin-bottom: 10px; height: 40px; }
    .stButton>button { font-size: 1.1rem !important; padding: 8px !important; margin-bottom: -12px !important; border-radius: 12px !important; height: 46px !important; }
    .stProgress { height: 4px !important; margin-bottom: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. TTS 함수 (영어 발음 고정) ---
def play_feedback(word, buzzer=False):
    safe_word = word.replace("'", "\\'")
    buzzer_js = "var ctx=new(window.AudioContext||window.webkitAudioContext)();var osc=ctx.createOscillator();var gain=ctx.createGain();osc.type='sawtooth';osc.frequency.setValueAtTime(150,ctx.currentTime);gain.gain.setValueAtTime(0.1,ctx.currentTime);osc.connect(gain);gain.connect(ctx.destination);osc.start();osc.stop(ctx.currentTime+0.3);" if buzzer else ""
    
    js_code = f"""
    <script>
    {buzzer_js}
    setTimeout(function() {{
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{safe_word}');
        var voices = window.speechSynthesis.getVoices();
        var enVoice = voices.find(v => v.lang === 'en-US' || v.name.includes('Google US English')) || voices.find(v => v.lang.startsWith('en'));
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
        target_list = [item for item in full_list if str(item.get('target', '')).upper() == 'Y']
        return full_list, target_list
    except: return [], []

full_data, target_data = load_all_data()

# --- 4. 세션 상태 관리 ---
keys = {
    'quiz_pool': [], 'incorrect_bucket': [], 'current_idx': 0, 
    'correct_ans': 0, 'is_finished': False, 'quiz_item': None, 
    'options': [], 'answered': False, 'show_card_meaning': False
}
for key, default in keys.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- 5. 학습 로직 함수들 ---
def start_new_round(words):
    if not words: return
    shuffled = words.copy()
    random.shuffle(shuffled)
    st.session_state.quiz_pool = shuffled
    st.session_state.incorrect_bucket = []
    st.session_state.current_idx = 0
    st.session_state.correct_ans = 0
    st.session_state.is_finished = False
    st.session_state.quiz_item = None
    st.session_state.answered = False
    st.session_state.show_card_meaning = False

def get_next_question():
    if st.session_state.current_idx < len(st.session_state.quiz_pool):
        item = st.session_state.quiz_pool[st.session_state.current_idx]
        others = random.sample([i for i in full_data if i['word'] != item['word']], min(4, len(full_data)-1))
        opts = [item] + others
        random.shuffle(opts)
        st.session_state.quiz_item = item
        st.session_state.options = opts
        st.session_state.answered = False
        st.session_state.show_card_meaning = False
    else:
        st.session_state.is_finished = True

def handle_answer(user_label, correct_label, quiz_obj, play_sound=True):
    """답변 처리 콜백: play_sound 옵션 추가"""
    if st.session_state.answered: return 
    st.session_state.answered = True
    
    is_correct = (user_label == correct_label)
    if is_correct:
        st.session_state.correct_ans += 1
    else:
        st.session_state.incorrect_bucket.append(quiz_obj)
    
    # 5초 카드 모드에서는 버튼 클릭 시 음성 재생을 건너뜀
    if play_sound:
        play_feedback(quiz_obj.get('word', ''), buzzer=not is_correct)

if not st.session_state.quiz_pool and target_data:
    start_new_round(target_data)

# --- 6. 메인 UI 구성 ---
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
        if st.session_state.quiz_item is None:
            get_next_question()
            if st.session_state.quiz_item is None: st.rerun()

        st.progress(st.session_state.current_idx / len(st.session_state.quiz_pool))
        mode = st.radio("", ["뜻→단어", "단어→뜻", "5초 카드"], horizontal=True, key="mode_select", label_visibility="collapsed")
        
        quiz = st.session_state.quiz_item

        # [모드 1] 5초 카드
        if mode == "5초 카드":
            st.markdown(f'<p class="main-word">{quiz.get("word", "")}</p>', unsafe_allow_html=True)
            
            if not st.session_state.show_card_meaning:
                # 단어가 처음 나올 때만 발음 재생
                play_feedback(quiz.get("word", ""))
                st.markdown('<p style="text-align:center; color:#888; height:40px;">뜻 생각 중... (5초)</p>', unsafe_allow_html=True)
                time.sleep(5)
                st.session_state.show_card_meaning = True
                st.rerun()
            else:
                st.markdown(f'<p class="meaning-reveal">{quiz.get("meaning", "")}</p>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                # O, X 버튼: play_sound=False로 설정하여 버튼 클릭 시 소리 방지
                if c1.button("⭕ 맞힘", use_container_width=True, key="c_ok", disabled=st.session_state.answered):
                    handle_answer("OK", "OK", quiz, play_sound=False)
                    time.sleep(0.5)
                    st.session_state.current_idx += 1
                    get_next_question(); st.rerun()
                if c2.button("❌ 틀림", use_container_width=True, key="c_no", disabled=st.session_state.answered):
                    handle_answer("NO", "OK", quiz, play_sound=False)
                    time.sleep(0.5)
                    st.session_state.current_idx += 1
                    get_next_question(); st.rerun()

        # [모드 2] 객관식
        else:
            is_word_to_mean = (mode == "단어→뜻")
            display_text = quiz.get('word', "") if is_word_to_mean else quiz.get('meaning', "")
            st.markdown(f'<p class="main-word">{display_text}</p>', unsafe_allow_html=True)
            correct_answer = quiz.get('meaning', "") if is_word_to_mean else quiz.get('word', "")
            
            for i, item in enumerate(st.session_state.options):
                label = item.get('meaning', "") if is_word_to_mean else item.get('word', "")
                if st.button(label, use_container_width=True, key=f"q_{i}", disabled=st.session_state.answered):
                    # 객관식 모드는 기존처럼 소리 재생
                    handle_answer(label, correct_answer, quiz, play_sound=True)
                    if label == correct_answer: st.success("정답!")
                    else: st.error(f"정답: {correct_answer}")
                    
                    time.sleep(1.2)
                    st.session_state.current_idx += 1
                    get_next_question(); st.rerun()

        st.caption(f"Progress: {st.session_state.current_idx + 1} / {len(st.session_state.quiz_pool)}")
