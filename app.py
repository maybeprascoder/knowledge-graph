import streamlit as st
import json, os,glob
from qa_anydoc_v2 import (
    load_text, load_triples, answer_from_triples,
    retrieve_sentences, compose_answer_from_snippets,
    MIN_RAG_SIM
)

st.set_page_config(page_title="KG + RAG QA", page_icon="🕸️", layout="wide")
st.title("🕸️ Knowledge Graph + RAG QA")

with st.sidebar:
    st.header("Inputs")
    txt_files = sorted(glob.glob("./input/*.txt"))
    json_files = sorted(glob.glob("./output/*_triples.json"))

    doc_path = st.selectbox("Document (.txt)", txt_files, index=txt_files.index("./input/complex_demo.txt") if "./input/complex_demo.txt" in txt_files else 0)
    triples_path = st.selectbox("Triples JSON", json_files, index=json_files.index("./output/complex_llm_triples.json") if "./output/complex_llm_triples.json" in json_files else 0)

    use_ollama = st.checkbox("Use Ollama to compose answers", value=False)
    model = st.text_input("Ollama model", value="llama3.2", disabled=not use_ollama)
    verbose = st.checkbox("Verbose scoring (console)", value=False)
    load_btn = st.button("Load")

if "text" not in st.session_state or load_btn:
    try:
        st.session_state.text = load_text(doc_path)
        st.session_state.triples = load_triples(triples_path)
        st.success(f"Loaded doc + triples ✅  (triples: {len(st.session_state.triples)})")
    except Exception as e:
        st.error(f"Failed to load: {e}")

q = st.text_input("Ask a question about the document", value="Who does Priya Raman report to?")
submit = st.button("Answer")

col_ans, col_sup = st.columns([2,1])

if submit and q.strip():
    text = st.session_state.get("text","")
    triples = st.session_state.get("triples", [])

    with st.spinner("Reasoning..."):
        # KG-first
        ans, used_triples, kg_score = answer_from_triples(q, triples, verbose=verbose)
        # RAG
        snippets, best_sim = retrieve_sentences(q, text, k=3, verbose=verbose)

        if not ans and best_sim < MIN_RAG_SIM:
            final = "I don't know from the given document."
        elif ans and use_ollama:
            final = compose_answer_from_snippets(q, snippets, used_triples, True, model)
        elif ans:
            final = ans
            if best_sim >= MIN_RAG_SIM and snippets:
                final += "  (Context: " + " | ".join(snippets[:2]) + ")"
        else:
            final = compose_answer_from_snippets(q, snippets, triples, use_ollama, model)

    with col_ans:
        st.subheader("Answer")
        st.write(final)
        st.caption(f"Debug: KG used={bool(used_triples)} | KG score={kg_score:.2f} | RAG best_sim={best_sim:.2f}")
    with col_sup:
        st.subheader("Support")
        if used_triples:
            st.markdown("**Triples**")
            for t in used_triples[:5]:
                st.caption(f"- {t['head_entity']['entity']} {t['relation']['relation']} {t['tail_entity']['entity']}")
        if snippets:
            st.markdown("**Snippets**")
            for s in snippets[:3]:
                st.caption(f"- {s}")
