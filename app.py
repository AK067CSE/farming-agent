"""
KisanMitra - AI-Powered Farming Advisory System
Complete rewrite: card layout, bold colors, animated loader, Enter-to-send
"""

import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import sys
import html
import markdown as md_lib
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import Runner, farming_agent, APP_NAME, USER_ID
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai import types as genai_types

# ──────────────────────────── Page config ────────────────────────────
st.set_page_config(
    page_title="KisanMitra — AI Farm Advisor",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────── CSS ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Playfair+Display:wght@700;800&display=swap');

:root {
    --green-900: #1a3d22;
    --green-800: #1e4d2b;
    --green-700: #2d6a3f;
    --green-600: #3a8050;
    --green-500: #4a9e63;
    --green-100: #e8f5ed;
    --green-50:  #f2faf4;
    --amber-600: #c97d1a;
    --amber-400: #f0a830;
    --amber-100: #fef3dc;
    --brown-900: #3b1f0a;
    --brown-700: #5c3314;
    --brown-500: #7d4a20;
    --brown-200: #d4b896;
    --brown-100: #f5e8d8;
    --brown-50:  #fdf6ec;
    --white:     #ffffff;
    --text-dark: #1a0f05;
    --text-mid:  #3d2409;
    --text-soft: #6b4c2a;
    --border:    #dcc9ad;
    --shadow-sm: 0 2px 8px rgba(59,31,10,.10);
    --shadow:    0 4px 20px rgba(59,31,10,.14);
    --shadow-lg: 0 10px 40px rgba(59,31,10,.20);
    --r:         16px;
}

/* ── Base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp {
    font-family: 'Nunito', sans-serif !important;
    background: var(--brown-50) !important;
    color: var(--text-dark) !important;
}
.stApp {
    background: linear-gradient(150deg, #fdf6ec 0%, #f4e8d2 60%, #ede0c8 100%) !important;
}

/* ── Hide chrome ── */
#MainMenu, header, footer { display: none !important; }
.block-container {
    padding: 1rem 1.5rem 1rem !important;
    max-width: 1000px !important;
}

/* ════════════ HEADER ════════════ */
.km-header {
    background: linear-gradient(135deg, var(--green-900) 0%, var(--green-800) 50%, var(--brown-700) 100%);
    border-radius: var(--r);
    padding: 18px 24px;
    margin-bottom: 18px;
    box-shadow: var(--shadow-lg);
    display: flex;
    align-items: center;
    gap: 16px;
}
.km-logo {
    width: 56px; height: 56px;
    background: rgba(255,255,255,.15);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem; flex-shrink: 0;
    border: 1px solid rgba(255,255,255,.2);
}
.km-htext { flex: 1; }
.km-hname {
    font-family: 'Playfair Display', serif;
    font-size: 2rem; font-weight: 800;
    color: #fff; margin: 0; line-height: 1.1;
    letter-spacing: -.3px;
}
.km-htag {
    font-size: .82rem; font-weight: 600;
    color: rgba(255,255,255,.7);
    margin: 4px 0 0; letter-spacing: .4px;
}
.km-hpills { display: flex; gap: 8px; flex-wrap: wrap; }
.km-pill {
    background: rgba(255,255,255,.15);
    border: 1px solid rgba(255,255,255,.25);
    color: rgba(255,255,255,.9);
    padding: 4px 12px; border-radius: 20px;
    font-size: .76rem; font-weight: 700; letter-spacing: .3px;
}

/* ════════════ MESSAGE CARD ════════════ */
.km-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--r);
    box-shadow: var(--shadow-sm);
    margin-bottom: 12px;
    overflow: hidden;
    transition: box-shadow .2s;
}
.km-card:hover { box-shadow: var(--shadow); }

/* User row */
.km-user-row {
    display: flex;
    align-items: flex-start;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 20px;
    background: linear-gradient(135deg, #fff8f0 0%, #fdf1e1 100%);
}
.km-user-bubble {
    background: linear-gradient(135deg, var(--brown-700) 0%, var(--brown-900) 100%);
    color: #fff;
    border-radius: 14px 14px 3px 14px;
    padding: 12px 16px;
    max-width: 72%;
    font-size: .95rem;
    font-weight: 700;
    line-height: 1.5;
    box-shadow: 0 3px 12px rgba(92,51,20,.35);
    word-break: break-word;
}
.km-user-label {
    font-size: .68rem; font-weight: 900;
    text-transform: uppercase; letter-spacing: .7px;
    color: rgba(255,255,255,.6);
    margin-bottom: 4px;
}
.km-user-av {
    width: 38px; height: 38px; flex-shrink: 0;
    background: linear-gradient(135deg, var(--brown-500), var(--brown-700));
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    box-shadow: 0 2px 8px rgba(92,51,20,.3);
    margin-top: 2px;
}

/* Bot row */
.km-bot-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 16px 20px;
    background: linear-gradient(135deg, var(--green-50) 0%, #edf7f0 100%);
    border-top: 1px solid #e0f0e4;
}
.km-bot-av {
    width: 38px; height: 38px; flex-shrink: 0;
    background: linear-gradient(135deg, var(--green-700), var(--green-500));
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    box-shadow: 0 2px 8px rgba(45,106,63,.3);
    margin-top: 2px;
}
.km-bot-content {
    flex: 1; min-width: 0;
}
.km-bot-label {
    font-size: .68rem; font-weight: 900;
    text-transform: uppercase; letter-spacing: .7px;
    color: var(--green-700);
    margin-bottom: 6px;
}

/* Markdown inside bot reply */
.km-bot-md {
    font-size: .97rem;
    line-height: 1.75;
    color: var(--text-dark);
    font-weight: 700;
}
.km-bot-md p {
    margin: 0 0 10px;
    font-weight: 700;
    color: var(--text-dark);
}
.km-bot-md p:last-child { margin: 0; }
.km-bot-md strong, .km-bot-md b {
    color: var(--green-900);
    font-weight: 900;
}
.km-bot-md ul {
    margin: 8px 0 12px 0;
    padding: 0;
    list-style: none;
}
.km-bot-md ul li {
    margin-bottom: 7px;
    font-weight: 700;
    padding-left: 22px;
    position: relative;
    color: var(--text-dark);
}
.km-bot-md ul li::before {
    content: "🌿";
    position: absolute; left: 0; top: 0;
    font-size: .8rem; line-height: 1.6;
}
.km-bot-md ol {
    margin: 8px 0 12px 0;
    padding-left: 24px;
}
.km-bot-md ol li {
    margin-bottom: 7px;
    font-weight: 700;
    color: var(--text-dark);
}
.km-bot-md ol li::marker {
    color: var(--green-700);
    font-weight: 900;
    font-size: 1rem;
}
.km-bot-md h1,.km-bot-md h2,.km-bot-md h3 {
    font-family: 'Playfair Display', serif;
    color: var(--green-800);
    margin: 14px 0 8px;
    font-weight: 800;
    border-bottom: 2px solid var(--green-100);
    padding-bottom: 4px;
}
.km-bot-md h1 { font-size: 1.25rem; }
.km-bot-md h2 { font-size: 1.1rem; }
.km-bot-md h3 { font-size: 1rem; }
.km-bot-md code {
    background: var(--green-100);
    color: var(--green-800);
    padding: 2px 7px; border-radius: 5px;
    font-size: .88em; font-weight: 700;
}
.km-bot-md pre {
    background: var(--green-50);
    border: 1px solid #c8e6cc;
    border-radius: 8px; padding: 12px;
    overflow-x: auto; margin: 10px 0;
}
.km-bot-md hr {
    border: none;
    border-top: 2px solid #c8e6cc;
    margin: 12px 0;
}
.km-bot-md blockquote {
    border-left: 4px solid var(--green-600);
    margin: 10px 0; padding: 8px 14px;
    background: var(--green-50);
    border-radius: 0 10px 10px 0;
    color: var(--text-mid);
    font-weight: 700;
}
.km-bot-md table {
    width: 100%; border-collapse: collapse; margin: 10px 0;
}
.km-bot-md th {
    background: var(--green-700); color: #fff;
    padding: 8px 12px; font-weight: 800; text-align: left;
}
.km-bot-md td {
    padding: 7px 12px; border-bottom: 1px solid #dceee0;
    font-weight: 700;
}
.km-bot-md tr:nth-child(even) td { background: var(--green-50); }

/* ════════════ LOADER CARD ════════════ */
.km-loader-card {
    background: linear-gradient(135deg, var(--green-50), #edf7f0);
    border: 1px solid var(--border);
    border-radius: var(--r);
    box-shadow: var(--shadow-sm);
    margin-bottom: 12px;
    padding: 20px 20px 20px 70px;
    position: relative;
}
.km-loader-av {
    position: absolute;
    left: 20px; top: 20px;
    width: 38px; height: 38px;
    background: linear-gradient(135deg, var(--green-700), var(--green-500));
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
}
.km-loader-label {
    font-size: .68rem; font-weight: 900;
    text-transform: uppercase; letter-spacing: .7px;
    color: var(--green-700); margin-bottom: 10px;
}
.km-typing {
    display: flex; gap: 5px; align-items: center;
}
.km-typing span {
    width: 9px; height: 9px;
    background: var(--green-600);
    border-radius: 50%;
    animation: bounce 1.2s infinite;
    display: inline-block;
}
.km-typing span:nth-child(2) { animation-delay: .2s; background: var(--green-500); }
.km-typing span:nth-child(3) { animation-delay: .4s; background: var(--amber-400); }
@keyframes bounce {
    0%,60%,100% { transform: translateY(0); opacity:.7; }
    30%          { transform: translateY(-8px); opacity:1; }
}
.km-thinking-text {
    margin-top: 7px;
    font-size: .82rem; font-weight: 700;
    color: var(--green-700);
    animation: pulse 1.8s infinite;
}
@keyframes pulse { 0%,100%{opacity:.5} 50%{opacity:1} }

/* ════════════ EMPTY STATE ════════════ */
.km-empty {
    text-align: center;
    padding: 60px 24px 50px;
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--r);
    box-shadow: var(--shadow-sm);
    margin-bottom: 12px;
}
.km-empty-icon { font-size: 3.8rem; margin-bottom: 14px; }
.km-empty-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem; font-weight: 700;
    color: var(--brown-700); margin-bottom: 8px;
}
.km-empty-sub {
    font-size: .9rem; font-weight: 600;
    color: var(--text-soft); line-height: 1.7; margin-bottom: 24px;
}
.km-chip-row { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.km-chip {
    background: var(--green-50);
    border: 1.5px solid #a8d9b4;
    color: var(--green-800);
    border-radius: 20px;
    padding: 7px 16px;
    font-size: .82rem; font-weight: 700;
}

/* ════════════ INPUT ════════════ */
.stTextArea > label { display: none !important; }
.stTextArea textarea {
    background: var(--white) !important;
    border: 2px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text-dark) !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: .97rem !important;
    font-weight: 700 !important;
    resize: none !important;
    padding: 14px 16px !important;
    transition: border-color .2s, box-shadow .2s;
    box-shadow: var(--shadow-sm) !important;
}
.stTextArea textarea::placeholder { color: #b89a78 !important; font-weight: 600 !important; }
.stTextArea textarea:focus {
    border-color: var(--green-600) !important;
    box-shadow: 0 0 0 3px rgba(58,128,80,.15) !important;
    outline: none !important;
}

/* SEND button */
[data-testid="stFormSubmitButton"] > button,
[data-testid="stFormSubmitButton"] > button:focus {
    background: linear-gradient(135deg, var(--green-700) 0%, var(--green-900) 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    padding: 14px 0 !important;
    letter-spacing: .4px !important;
    box-shadow: 0 4px 16px rgba(30,77,43,.4) !important;
    transition: all .2s !important;
    cursor: pointer !important;
    width: 100% !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, var(--green-900) 0%, #0f2714 100%) !important;
    box-shadow: 0 6px 24px rgba(30,77,43,.55) !important;
    transform: translateY(-2px) !important;
}

.km-hint {
    text-align: right;
    font-size: .72rem; font-weight: 700;
    color: var(--text-soft); margin-top: 5px;
    letter-spacing: .2px;
}

/* ════════════ SIDEBAR ════════════ */
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(175deg, #f5e8d3 0%, #ebd9be 100%) !important;
    border-right: 2px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container { padding: .8rem .9rem 1rem !important; }

.km-sc {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: 12px;
    padding: 14px 14px;
    margin-bottom: 11px;
    box-shadow: var(--shadow-sm);
}
.km-sc-title {
    font-family: 'Playfair Display', serif;
    font-size: .95rem; font-weight: 700;
    color: var(--brown-700);
    margin-bottom: 10px; padding-bottom: 7px;
    border-bottom: 1.5px solid #e8d9c4;
}

.km-stats { display: flex; gap: 8px; margin-bottom: 10px; }
.km-stat {
    flex: 1; background: var(--brown-50);
    border: 1.5px solid #e0ccb0;
    border-radius: 10px; padding: 10px 8px; text-align: center;
}
.km-stat-val {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem; color: var(--green-700);
    font-weight: 700; line-height: 1;
}
.km-stat-lbl {
    font-size: .69rem; font-weight: 700;
    color: var(--text-soft); margin-top: 3px; letter-spacing: .2px;
}

.km-season {
    background: linear-gradient(135deg, var(--amber-400), var(--amber-600));
    color: #fff; padding: 3px 12px; border-radius: 20px;
    font-size: .76rem; font-weight: 800; letter-spacing: .4px;
}

/* Sidebar buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--green-700) 0%, var(--green-900) 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 9px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    font-size: .88rem !important;
    padding: 9px 14px !important;
    transition: all .18s !important;
    box-shadow: 0 2px 8px rgba(30,77,43,.25) !important;
    text-align: left !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, var(--green-900) 0%, #0f2714 100%) !important;
    transform: translateX(3px) !important;
    box-shadow: 0 4px 14px rgba(30,77,43,.35) !important;
}
[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, var(--amber-400) 0%, var(--amber-600) 100%) !important;
    color: #fff !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, var(--amber-600) 0%, #a06510 100%) !important;
    transform: translateX(3px) !important;
}

.stTextInput > label { display: none !important; }
.stTextInput input {
    background: var(--brown-50) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-dark) !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: .88rem !important;
    font-weight: 700 !important;
    padding: 9px 12px !important;
}
.stTextInput input:focus {
    border-color: var(--green-600) !important;
    box-shadow: 0 0 0 3px rgba(58,128,80,.12) !important;
}

/* Streamlit spinner hide — we use custom loader */
.stSpinner { display: none !important; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Enter key via components.html (this actually runs JS!) ────────────
components.html("""
<script>
(function() {
    function bind() {
        var areas = window.parent.document.querySelectorAll('textarea');
        areas.forEach(function(ta) {
            if (ta._km) return;
            ta._km = true;
            ta.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    var form = ta.closest('form');
                    if (!form) return;
                    var btn = form.querySelector('button[kind="primaryFormSubmit"]')
                           || form.querySelector('button[type="submit"]')
                           || form.querySelector('button');
                    if (btn) btn.click();
                }
            });
        });
    }
    // Poll until textarea appears
    var tries = 0;
    var iv = setInterval(function() {
        bind();
        tries++;
        if (tries > 40) clearInterval(iv);
    }, 300);
})();
</script>
""", height=0)


# ──────────────────────────── Session state ──────────────────────────
def _init():
    defaults = {
        'messages':        [],
        'user_name':       'Farmer',
        'session_created': False,
        'session_id':      f"km_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.getpid()}",
        'loading':         False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
_init()


# ──────────────────────────── Services ───────────────────────────────
@st.cache_resource
def _services():
    ss = InMemorySessionService()
    ms = InMemoryMemoryService()
    r  = Runner(agent=farming_agent, app_name=APP_NAME,
                session_service=ss, memory_service=ms)
    return ss, ms, r


async def _ensure_session(ss):
    if st.session_state.session_created:
        return
    try:
        await ss.create_session(
            app_name=APP_NAME, user_id=USER_ID,
            session_id=st.session_state.session_id,
            state={"user:name": st.session_state.user_name,
                   "current_task": "farming_advice"},
        )
    except Exception as e:
        if "already exists" not in str(e).lower():
            raise
    st.session_state.session_created = True


async def _call_agent(text, ss, ms, runner) -> str:
    try:
        await _ensure_session(ss)
        content = genai_types.Content(role="user",
                                      parts=[genai_types.Part(text=text)])
        final = ""
        async for ev in runner.run_async(user_id=USER_ID,
                                         session_id=st.session_state.session_id,
                                         new_message=content):
            if ev.is_final_response():
                if ev.content and ev.content.parts:
                    for p in ev.content.parts:
                        if hasattr(p, "text") and p.text:
                            final += p.text
                break
        try:
            sess = await ss.get_session(app_name=APP_NAME, user_id=USER_ID,
                                        session_id=st.session_state.session_id)
            await ms.add_session_to_memory(sess)
        except Exception:
            pass
        return final or "(No response received)"
    except Exception as e:
        return f"⚠️ Error: {e}"


# ──────────────────────────── Helpers ─────────────────────────────────
def _season():
    m = datetime.now().month
    if 6 <= m <= 9:  return "🌧️ Kharif Season"
    if 10 <= m <= 3: return "🌾 Rabi Season"
    return "☀️ Zaid Season"


QUICK = [
    ("🌱", "Best crop for this season"),
    ("🌦️", "Weather impact on farming"),
    ("🐛", "Pest & disease control"),
    ("💰", "Today's market prices"),
    ("🏛️", "Government schemes"),
    ("💧", "Irrigation tips"),
]


# ──────────────────────────── Chat render ─────────────────────────────
def _md_to_html(text: str) -> str:
    """Convert markdown text to HTML with extensions."""
    return md_lib.markdown(
        text,
        extensions=["nl2br", "tables", "fenced_code", "sane_lists"]
    )


def _render_messages():
    all_html = ""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            safe = html.escape(msg["content"]).replace("\n", "<br>")
            name = html.escape(st.session_state.user_name).upper()
            all_html += f"""
            <div class="km-card">
              <div class="km-user-row">
                <div class="km-user-bubble">
                  <div class="km-user-label">{name}</div>
                  {safe}
                </div>
                <div class="km-user-av">👤</div>
              </div>
            </div>"""
        else:
            # Convert markdown → HTML so it stays inside the card
            content_html = _md_to_html(msg["content"])
            all_html += f"""
            <div class="km-card">
              <div class="km-bot-row">
                <div class="km-bot-av">🌿</div>
                <div class="km-bot-content">
                  <div class="km-bot-label">KisanMitra</div>
                  <div class="km-bot-md">{content_html}</div>
                </div>
              </div>
            </div>"""
    if all_html:
        st.markdown(all_html, unsafe_allow_html=True)


def _render_loader():
    st.markdown("""
    <div class="km-loader-card">
      <div class="km-loader-av">🌿</div>
      <div class="km-bot-label">KisanMitra</div>
      <div class="km-typing">
        <span></span><span></span><span></span>
      </div>
      <div class="km-thinking-text">Researching your query…</div>
    </div>""", unsafe_allow_html=True)


def _render_empty():
    st.markdown("""
    <div class="km-empty">
      <div class="km-empty-icon">🌾</div>
      <div class="km-empty-title">Namaste! I'm KisanMitra</div>
      <div class="km-empty-sub">
        Your AI-powered farming companion for India.<br>
        Ask me about crops, soil, weather, market prices, or government schemes.
      </div>
      <div class="km-chip-row">
        <span class="km-chip">🌱 Crop Planning</span>
        <span class="km-chip">🌦️ Weather</span>
        <span class="km-chip">💰 Market Prices</span>
        <span class="km-chip">🏛️ Govt Schemes</span>
        <span class="km-chip">💧 Irrigation</span>
        <span class="km-chip">🐛 Pest Control</span>
      </div>
    </div>""", unsafe_allow_html=True)


# ──────────────────────────── Sidebar ─────────────────────────────────
def _sidebar():
    with st.sidebar:
        # Brand
        st.markdown("""
        <div style="text-align:center;padding:10px 0 18px;">
          <div style="font-size:2.4rem;margin-bottom:6px;">🌿</div>
          <div style="font-family:'Playfair Display',serif;font-size:1.4rem;
                      font-weight:800;color:#2d6a3f;line-height:1.1;">KisanMitra</div>
          <div style="font-size:.73rem;font-weight:700;color:#6b4c2a;margin-top:4px;
                      letter-spacing:.3px;">Your AI Farm Companion</div>
        </div>""", unsafe_allow_html=True)

        msgs    = st.session_state.messages
        queries = len([m for m in msgs if m["role"] == "user"])

        st.markdown(f"""
        <div class="km-sc">
          <div class="km-sc-title">📊 Session</div>
          <div class="km-stats">
            <div class="km-stat">
              <div class="km-stat-val">{len(msgs)}</div>
              <div class="km-stat-lbl">Messages</div>
            </div>
            <div class="km-stat">
              <div class="km-stat-val">{queries}</div>
              <div class="km-stat-lbl">Queries</div>
            </div>
          </div>
          <div style="font-size:.8rem;font-weight:700;color:#6b4c2a;">
            Season: <span class="km-season">{_season()}</span>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="km-sc"><div class="km-sc-title">⚙️ Your Profile</div>',
                    unsafe_allow_html=True)
        new_name = st.text_input("name", value=st.session_state.user_name,
                                 key="nm_inp", label_visibility="collapsed")
        if new_name and new_name != st.session_state.user_name:
            st.session_state.user_name = new_name
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="km-sc"><div class="km-sc-title">⚡ Quick Topics</div>',
                    unsafe_allow_html=True)
        for icon, label in QUICK:
            if st.button(f"{icon}  {label}", key=f"q_{label}", use_container_width=True):
                st.session_state["_inject"] = label
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="km-sc"><div class="km-sc-title">🗂️ Actions</div>',
                    unsafe_allow_html=True)
        if st.button("🗑️  Clear Conversation", key="clr", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        if msgs:
            lines = []
            for m in msgs:
                who = st.session_state.user_name if m["role"] == "user" else "KisanMitra"
                lines.append(f"[{m.get('timestamp','')}] {who}: {m['content']}")
            st.download_button(
                "📥  Download Chat", data="\n".join(lines),
                file_name=f"kisanmitra_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain", use_container_width=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────── Main ────────────────────────────────────
def main():
    ss, ms, runner = _services()
    injected = st.session_state.pop("_inject", None)

    # Header (no season badge in header)
    st.markdown("""
    <div class="km-header">
      <div class="km-logo">🌿</div>
      <div class="km-htext">
        <div class="km-hname">KisanMitra</div>
        <div class="km-htag">AI-POWERED AGRICULTURAL ADVISORY SYSTEM FOR INDIA</div>
      </div>
      <div class="km-hpills">
        <span class="km-pill">🌱 Crops</span>
        <span class="km-pill">🌦️ Weather</span>
        <span class="km-pill">💰 Market</span>
        <span class="km-pill">🏛️ Schemes</span>
      </div>
    </div>""", unsafe_allow_html=True)

    # Messages or empty state
    if not st.session_state.messages and not st.session_state.get("loading"):
        _render_empty()
    else:
        _render_messages()
        if st.session_state.get("loading"):
            _render_loader()

    # Input form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "input",
            value=injected or "",
            height=88,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("🚀  Send Message", use_container_width=True)

    st.markdown(
        '<div class="km-hint">⏎ Enter to send &nbsp;·&nbsp; Shift+Enter for new line</div>',
        unsafe_allow_html=True,
    )

    if submitted and user_input and user_input.strip():
        text = user_input.strip()
        ts   = datetime.now().strftime("%H:%M")

        st.session_state.messages.append(
            {"role": "user", "content": text, "timestamp": ts}
        )
        st.session_state.loading = True
        st.rerun()

    # If loading flag is set, call the agent now
    if st.session_state.get("loading"):
        last_user = next(
            (m["content"] for m in reversed(st.session_state.messages)
             if m["role"] == "user"), None
        )
        if last_user:
            response = asyncio.run(_call_agent(last_user, ss, ms, runner))
            st.session_state.messages.append(
                {"role": "assistant", "content": response,
                 "timestamp": datetime.now().strftime("%H:%M")}
            )
        st.session_state.loading = False
        st.rerun()

    _sidebar()


if __name__ == "__main__":
    main()