import base64
import json
import os
import uuid
from html import escape as esc

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "tasks.json")
HERO_IMAGE_FILE = os.path.join(BASE_DIR, "iM금융지주_대표이미지.png")

CATEGORIES = ["프로세스", "컨텐츠", "QA"]
CATEGORY_COLORS = {
    "프로세스": ("#e8ecff", "#5b6bd9"),
    "컨텐츠": ("#ffeee0", "#d9822f"),
    "QA": ("#e2f7ee", "#269b6b"),
}
TEXT_MAX_LEN = 200
MEMO_MAX_LEN = 500


# ----------------------------------------------------------------------------
# Persistence (JSON file on disk == localStorage equivalent for a Python app)
# ----------------------------------------------------------------------------
def sanitize_task(raw):
    if not isinstance(raw, dict):
        return None
    text = str(raw.get("text", "")).strip()
    if not text:
        return None
    return {
        "id": raw.get("id") or str(uuid.uuid4()),
        "text": text[:TEXT_MAX_LEN],
        "category": raw.get("category") if raw.get("category") in CATEGORIES else CATEGORIES[0],
        "memo": str(raw.get("memo", ""))[:MEMO_MAX_LEN],
        "completed": bool(raw.get("completed", False)),
    }


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return [t for t in (sanitize_task(item) for item in data) if t]
    except (json.JSONDecodeError, OSError):
        return []


def save_tasks(tasks):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except OSError as e:
        st.warning(f"할 일 데이터를 저장하지 못했습니다: {e}")


@st.cache_data
def get_base64_image(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None
if "edit_error" not in st.session_state:
    st.session_state.edit_error = False


# ----------------------------------------------------------------------------
# Callbacks
# ----------------------------------------------------------------------------
def add_task():
    text = st.session_state.get("new_text", "").strip()
    if not text:
        st.session_state.add_error = True
        return
    st.session_state.add_error = False
    st.session_state.tasks.append(
        {
            "id": str(uuid.uuid4()),
            "text": text[:TEXT_MAX_LEN],
            "category": st.session_state.get("new_category") or CATEGORIES[0],
            "memo": st.session_state.get("new_memo", "").strip()[:MEMO_MAX_LEN],
            "completed": False,
        }
    )
    save_tasks(st.session_state.tasks)
    st.session_state.new_text = ""
    st.session_state.new_memo = ""


def toggle_task(task_id):
    for t in st.session_state.tasks:
        if t["id"] == task_id:
            t["completed"] = not t["completed"]
            break
    save_tasks(st.session_state.tasks)


def delete_task(task_id):
    st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task_id]
    if st.session_state.editing_id == task_id:
        st.session_state.editing_id = None
    save_tasks(st.session_state.tasks)


def start_edit(task):
    st.session_state.editing_id = task["id"]
    st.session_state.edit_error = False
    st.session_state[f"edit_text_{task['id']}"] = task["text"]
    st.session_state[f"edit_cat_{task['id']}"] = task["category"]
    st.session_state[f"edit_memo_{task['id']}"] = task["memo"]


def cancel_edit():
    st.session_state.editing_id = None
    st.session_state.edit_error = False


def save_edit(task_id):
    new_text = st.session_state.get(f"edit_text_{task_id}", "").strip()
    if not new_text:
        st.session_state.edit_error = True
        return
    for t in st.session_state.tasks:
        if t["id"] == task_id:
            t["text"] = new_text[:TEXT_MAX_LEN]
            t["category"] = st.session_state.get(f"edit_cat_{task_id}", t["category"])
            t["memo"] = st.session_state.get(f"edit_memo_{task_id}", "").strip()[:MEMO_MAX_LEN]
            break
    st.session_state.editing_id = None
    st.session_state.edit_error = False
    save_tasks(st.session_state.tasks)


# ----------------------------------------------------------------------------
# Page config & styles
# ----------------------------------------------------------------------------
st.set_page_config(page_title="My To-Do", page_icon="📝", layout="centered")

hero_b64 = get_base64_image(HERO_IMAGE_FILE)
hero_bg = f"url('data:image/png;base64,{hero_b64}')" if hero_b64 else "none"

st.markdown(
    f"""
    <style>
    .block-container {{
        max-width: 640px;
        padding-top: 2rem;
    }}

    .hero-banner {{
        position: relative;
        border-radius: 16px;
        overflow: hidden;
        background-image: {hero_bg};
        background-size: cover;
        background-position: center 15%;
        background-repeat: no-repeat;
        background-color: #14151c;
        padding: 48px 16px;
        text-align: center;
        margin-bottom: 1.2rem;
    }}
    .hero-banner::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, rgba(10,12,20,0.55), rgba(10,12,20,0.72));
    }}
    .hero-banner h1, .hero-banner p {{
        position: relative;
        z-index: 1;
        margin: 0;
    }}
    .hero-banner h1 {{
        color: #ffffff;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 8px rgba(0,0,0,0.35);
    }}
    .hero-banner p {{
        color: rgba(255,255,255,0.85);
        font-size: 13.5px;
        margin-top: 6px;
    }}

    .todo-card {{
        border: 1px solid #eaebef;
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 8px;
        background-color: #ffffff;
    }}
    .todo-card.completed {{
        opacity: 0.55;
    }}
    .todo-top-line {{
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }}
    .category-tag {{
        font-size: 11px;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 999px;
        white-space: nowrap;
    }}
    .todo-text {{
        font-size: 15px;
        font-weight: 500;
        overflow-wrap: anywhere;
    }}
    .todo-text.done {{
        text-decoration: line-through;
        color: #9498a3;
    }}
    .todo-memo {{
        margin-top: 5px;
        font-size: 12.5px;
        line-height: 1.5;
        color: #9498a3;
        overflow-wrap: anywhere;
        white-space: pre-wrap;
    }}
    .empty-state {{
        text-align: center;
        color: #9498a3;
        font-size: 14px;
        padding: 48px 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-banner">
        <h1>My To-Do</h1>
        <p>오늘 할 일을 관리해 보세요</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Progress bar
# ----------------------------------------------------------------------------
total = len(st.session_state.tasks)
done = sum(1 for t in st.session_state.tasks if t["completed"])
percent = round((done / total) * 100) if total else 0

with st.container(border=True):
    top_col1, top_col2 = st.columns([3, 1])
    top_col1.markdown(f"**{done} / {total} 완료**")
    top_col2.markdown(f"<div style='text-align:right; font-weight:800; color:#6c7ef5;'>{percent}%</div>", unsafe_allow_html=True)
    st.progress(percent / 100)


# ----------------------------------------------------------------------------
# Add form
# ----------------------------------------------------------------------------
with st.container(border=True):
    if "new_category" not in st.session_state:
        st.session_state.new_category = CATEGORIES[0]
    st.segmented_control(
        "카테고리",
        CATEGORIES,
        key="new_category",
        label_visibility="collapsed",
    )
    st.text_input(
        "할 일",
        key="new_text",
        placeholder="할 일을 입력하세요",
        max_chars=TEXT_MAX_LEN,
        label_visibility="collapsed",
    )
    st.text_area(
        "메모",
        key="new_memo",
        placeholder="메모 (선택 사항)",
        max_chars=MEMO_MAX_LEN,
        height=68,
        label_visibility="collapsed",
    )
    st.button("+ 추가", on_click=add_task, use_container_width=True, type="primary")
    if st.session_state.get("add_error"):
        st.warning("할 일 내용을 입력해주세요.")


# ----------------------------------------------------------------------------
# Task list
# ----------------------------------------------------------------------------
if not st.session_state.tasks:
    st.markdown(
        '<div class="empty-state">🗒️<br>아직 할 일이 없습니다.</div>',
        unsafe_allow_html=True,
    )
else:
    for task in st.session_state.tasks:
        if task["id"] == st.session_state.editing_id:
            with st.container(border=True):
                st.text_input("할 일", key=f"edit_text_{task['id']}", max_chars=TEXT_MAX_LEN, label_visibility="collapsed")
                st.selectbox("카테고리", CATEGORIES, key=f"edit_cat_{task['id']}", label_visibility="collapsed")
                st.text_area("메모", key=f"edit_memo_{task['id']}", max_chars=MEMO_MAX_LEN, height=68, label_visibility="collapsed")
                if st.session_state.edit_error:
                    st.warning("할 일 내용을 입력해주세요.")
                b1, b2 = st.columns(2)
                b1.button("저장", key=f"save_{task['id']}", on_click=save_edit, args=(task["id"],), use_container_width=True, type="primary")
                b2.button("취소", key=f"cancel_{task['id']}", on_click=cancel_edit, use_container_width=True)
        else:
            bg, fg = CATEGORY_COLORS[task["category"]]
            card_class = "todo-card completed" if task["completed"] else "todo-card"
            text_class = "todo-text done" if task["completed"] else "todo-text"
            memo_html = f'<div class="todo-memo">{esc(task["memo"])}</div>' if task["memo"] else ""

            row = st.columns([0.08, 0.72, 0.1, 0.1], vertical_alignment="center")
            row[0].checkbox(
                "완료",
                value=task["completed"],
                key=f"chk_{task['id']}",
                on_change=toggle_task,
                args=(task["id"],),
                label_visibility="collapsed",
            )
            row[1].markdown(
                f"""
                <div class="{card_class}" style="border:none; padding:0; margin:0;">
                    <div class="todo-top-line">
                        <span class="category-tag" style="background:{bg};color:{fg};">{esc(task['category'])}</span>
                        <span class="{text_class}">{esc(task['text'])}</span>
                    </div>
                    {memo_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
            row[2].button("✎", key=f"edit_{task['id']}", on_click=start_edit, args=(task,), help="수정")
            row[3].button("✕", key=f"del_{task['id']}", on_click=delete_task, args=(task["id"],), help="삭제")
            st.divider()
