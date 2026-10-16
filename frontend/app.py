"""Streamlit chat UI for the HR bot.

Login screen calls bot_backend /auth/login.
Chat screen calls bot_backend /chat with the JWT.

Run with:
    streamlit run frontend/app.py
"""
import os
import uuid

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# --- Config ---------------------------------------------------------------
BOT_BACKEND = os.getenv("BOT_BACKEND_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 240.0  # generous — LLM calls take a few seconds

st.set_page_config(page_title="HR Support Bot", page_icon="🤖", layout="centered")


# --- Session state defaults ----------------------------------------------
def _init_state() -> None:
    defaults = {
        "token": None,
        "emp_code": None,
        "role": None,
        "session_id": None,
        "messages": [],       # list of {"role": "user"|"assistant", "content": str}
        "intent": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()


# --- API helpers ----------------------------------------------------------
def api_login(email: str, password: str) -> dict:
    """POST /auth/login. Raises httpx.HTTPStatusError on bad credentials."""
    r = httpx.post(
        f"{BOT_BACKEND}/auth/login",
        json={"email": email, "password": password},
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def api_chat(message: str, session_id: str) -> dict:
    """POST /chat with the JWT from session state."""
    r = httpx.post(
        f"{BOT_BACKEND}/chat",
        json={"message": message, "session_id": session_id},
        headers={"Authorization": f"Bearer {st.session_state.token}"},
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


# --- Login screen ---------------------------------------------------------
def render_login() -> None:
    st.title("🤖 HR Support Bot")
    st.caption("Sign in with your company email.")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="bob@company.com")
        password = st.text_input("Password", type="password", placeholder="password123")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        if not email or not password:
            st.error("Please enter both email and password.")
            return
        try:
            data = api_login(email, password)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                st.error("Invalid email or password.")
            else:
                st.error(f"Login failed: {e.response.text}")
            return
        except httpx.RequestError as e:
            st.error(f"Cannot reach the bot backend at {BOT_BACKEND}. Is it running? ({e})")
            return

        # Store auth + reset chat state.
        st.session_state.token = data["access_token"]
        st.session_state.emp_code = data["emp_code"]
        st.session_state.role = data["role"]
        st.session_state.session_id = uuid.uuid4().hex[:8]
        st.session_state.messages = []
        st.session_state.intent = None
        st.rerun()

    st.info(
        "**Demo accounts** — all with password `password123`:\n"
        "- `bob@company.com` (employee, E002)\n"
        "- `alice@company.com` (employee, E001)\n"
        "- `david@company.com` (hr, E004)"
    )


# --- Chat screen ----------------------------------------------------------
def render_chat() -> None:
    with st.sidebar:
        st.markdown(f"**Signed in as** `{st.session_state.emp_code}`")
        st.markdown(f"**Role:** `{st.session_state.role}`")
        st.markdown(f"**Session:** `{st.session_state.session_id}`")
        if st.session_state.intent:
            st.markdown(f"**Last intent:** `{st.session_state.intent}`")
        st.divider()
        if st.button("Log out"):
            for k in ("token", "emp_code", "role", "session_id", "messages", "intent"):
                st.session_state[k] = None if k != "messages" else []
            st.rerun()

    st.title("🤖 HR Support Bot")
    st.caption(
        "Ask about payslips, leave balance, attendance, holidays, "
        "your manager or team. Data shown is only yours."
    )

    # Replay history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input box
    prompt = st.chat_input("Type your question...")
    if not prompt:
        return

    # Show the user's message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                data = api_chat(prompt, st.session_state.session_id)
                reply = data["reply"]
                st.session_state.intent = data.get("intent")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    st.error("Your session expired. Please log in again.")
                    st.session_state.token = None
                else:
                    st.error(f"Backend error: {e.response.text}")
                reply = None
            except httpx.RequestError as e:
                st.error(f"Cannot reach the bot backend at {BOT_BACKEND}. ({e})")
                reply = None

        if reply is not None:
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})


# --- Main -----------------------------------------------------------------
if st.session_state.token:
    render_chat()
else:
    render_login()