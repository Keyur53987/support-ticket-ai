import streamlit as st
import requests
import os

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Support Ticket AI", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

def login(email, password):
    response = requests.post(f"{API_URL}/login", data={"username": email, "password": password})
    if response.status_code == 200:
        st.session_state.token = response.json()["access_token"]
        st.session_state.user = requests.get(f"{API_URL}/me", headers={"Authorization": f"Bearer {st.session_state.token}"}).json()
        st.success("Logged in successfully!")
        st.rerun()
    else:
        st.error("Login failed. Check your credentials.")

def register(email, password):
    response = requests.post(f"{API_URL}/register", json={"email": email, "password": password})
    if response.status_code == 200:
        st.success("Registered successfully! Please log in.")
    else:
        st.error(f"Registration failed: {response.text}")

def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.rerun()

if not st.session_state.token:
    st.title("Welcome to Support Ticket AI")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            if submit:
                login(email, password)
                
    with tab2:
        with st.form("register_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Register")
            if submit:
                register(email, password)
else:
    st.sidebar.title(f"Hello, {st.session_state.user['email']}")
    if st.sidebar.button("Logout"):
        logout()
        
    st.title("Support Ticket Dashboard")
    tab1, tab2 = st.tabs(["New Ticket", "Ticket History"])
    
    with tab1:
        st.subheader("Submit a Support Ticket")
        with st.form("ticket_form"):
            message = st.text_area("What is the issue?", height=150)
            submit = st.form_submit_button("Submit Ticket")
            
            if submit and message:
                with st.spinner("AI is analyzing your ticket and searching policies..."):
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    response = requests.post(f"{API_URL}/tickets", json={"message": message}, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        decision = data.get("decision", {})
                        
                        st.subheader("AI Decision")
                        
                        action_col, conf_col = st.columns(2)
                        with action_col:
                            st.metric("Action", decision.get("action", "UNKNOWN"))
                        with conf_col:
                            st.metric("Confidence", f"{decision.get('confidence', 0.0) * 100:.1f}%")
                            
                        st.info(f"**Reasoning:** {decision.get('reason', '')}")
                        
                        sources = decision.get("sources", [])
                        if sources:
                            st.write("**Sources Cited:**")
                            for source in sources:
                                st.caption(f"- {source}")
                    else:
                        st.error(f"Failed to submit ticket: {response.text}")
                        
    with tab2:
        st.subheader("Your Ticket History")
        if st.button("Refresh History"):
            pass # Reruns and fetches below
            
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(f"{API_URL}/tickets", headers=headers)
        
        if response.status_code == 200:
            tickets = response.json()
            if not tickets:
                st.write("No tickets found.")
            for t in reversed(tickets):
                with st.expander(f"Ticket #{t['id']} - {t['message'][:50]}..."):
                    st.write("**Message:**")
                    st.write(t['message'])
                    st.write("---")
                    decision = t.get('decision')
                    if decision:
                        st.write(f"**Action:** {decision.get('action')}")
                        st.write(f"**Confidence:** {decision.get('confidence')}")
                        st.write(f"**Reasoning:** {decision.get('reason')}")
                        st.write(f"**Sources:** {', '.join(decision.get('sources', []))}")
                    else:
                        st.write("No decision recorded.")
        else:
            st.error("Failed to load ticket history.")
