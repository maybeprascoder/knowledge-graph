import streamlit as st
import requests

st.set_page_config(page_title="Knowledge Graph QA", layout="centered")
st.title("Knowledge Graph QA")

api_base = "http://localhost:8000"

mode = st.radio("Scope", ["All data", "By employee"], horizontal=True)

employee_id = ""
if mode == "By employee":
    employee_id = st.text_input("Employee ID (e.g., email)", "")

question = st.text_area("Your question", "What are the largest expenses and who approved them?")

if st.button("Ask") and question:
    try:
        with st.spinner("Thinking..."):
            if mode == "By employee" and employee_id:
                r = requests.get(f"{api_base}/qa/employee/{employee_id}", params={"q": question}, timeout=120)
            else:
                r = requests.get(f"{api_base}/qa", params={"q": question}, timeout=120)

        if r.ok:
            data = r.json()
            st.subheader("Answer")
            st.write(data.get("answer", ""))
            with st.expander("Context (raw)"):
                st.json(data.get("context", {}))
        else:
            st.error(f"Error: {r.status_code} - {r.text}")
    except Exception as e:
        st.error(str(e))