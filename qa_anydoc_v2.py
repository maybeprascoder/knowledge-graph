# qa_anydoc_v2.py
# QA over any document via KG-first + RAG fallback, with confidence thresholds.
# Usage examples at bottom.

import argparse, json, os, re, sys
from typing import List, Dict, Tuple, Optional

# -----------------------
# Config / thresholds
# -----------------------
MIN_KG_SCORE = 0.55   # min score to accept a KG-based answer (0..1)
MIN_RAG_SIM  = 0.15   # min Jaccard sim of best sentence to accept RAG answer

# -----------------------
# Optional deps
# -----------------------
try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except Exception:
    _NLP = None

try:
    import ollama
    HAVE_OLLAMA = True
except Exception:
    HAVE_OLLAMA = False

# -----------------------
# I/O helpers
# -----------------------
def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def load_triples(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# -----------------------
# Text utils
# -----------------------
_WORD_RE = re.compile(r"[A-Za-z0-9_]+")

def tokenize(s: str) -> List[str]:
    return _WORD_RE.findall(s.lower())

def lemma_or_lower(s: str) -> str:
    if not s: return s
    if _NLP:
        doc = _NLP(s)
        return " ".join(t.lemma_.lower() for t in doc if t.lemma_)
    return s.lower()

def jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb: return 0.0
    return len(sa & sb) / len(sa | sb)

def token_overlap(a: str, b: str) -> float:
    A, B = set(tokenize(a)), set(tokenize(b))
    return 0.0 if not A or not B else len(A & B) / len(A | B)

def normalize_rel(r: str) -> str:
    r = r.lower().replace(" ", "_")
    # friendly aliases (add more as you see them)
    r = r.replace("report_to", "reports_to").replace("reporting_to", "reports_to")
    return r

def is_entity_def_question(q: str) -> Optional[str]:
    ql = q.lower().strip(" ?!.")
    # patterns like "who is X", "what is X", "where is X"
    for prefix in ("who is ", "what is ", "where is ", "who was ", "what was ", "where was "):
        if ql.startswith(prefix):
            return q.strip()[len(prefix):].strip()
    return None

def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[\.\?\!])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]

# -----------------------
# KG-first answering
# -----------------------
def answer_from_triples(question: str, triples: List[Dict], verbose=False) -> Tuple[Optional[str], List[Dict], float]:
    q_lem = lemma_or_lower(question)
    q_tokens = tokenize(q_lem)

    scored: List[Tuple[float, Dict]] = []
    for t in triples:
        rel = normalize_rel(t["relation"]["relation"])
        head = t["head_entity"]["entity"]
        tail = t["tail_entity"]["entity"]

        # relation similarity (tokens vs question)
        rel_sim = jaccard(tokenize(rel), q_tokens)

        # entity-mention bonus using token overlap (so "Priya Raman" matches even if head has extra words)
        ent_bonus = max(
            token_overlap(question, head),
            token_overlap(question, tail)
        )
        # scale the bonus so even partial matches help but don't dominate
        ent_bonus = 0.5 if ent_bonus >= 0.30 else (0.25 if ent_bonus >= 0.20 else 0.0)

        score = rel_sim + ent_bonus
        if score > 0:
            scored.append((score, {
                "relation": {"relation": rel},
                "head_entity": t["head_entity"],
                "tail_entity": t["tail_entity"]
            }))

    if not scored:
        if verbose: print("KG: no candidate triples")
        return None, [], 0.0

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_trip = scored[0]
    if verbose:
        print(f"KG: best_score={best_score:.3f} rel={best_trip['relation']['relation']} "
              f"head={best_trip['head_entity']['entity']} tail={best_trip['tail_entity']['entity']}")

    if best_score < MIN_KG_SCORE:
        if verbose: print(f"KG: below threshold ({best_score:.3f} < {MIN_KG_SCORE})")
        return None, [], best_score

    # simple NL rendering
    rel0  = best_trip["relation"]["relation"].replace("_", " ")
    head0 = best_trip["head_entity"]["entity"]
    tail0 = best_trip["tail_entity"]["entity"]
    answer = f"{head0} {rel0} {tail0}."

    # top few as support
    support = [t for _, t in scored[:5]]
    return answer, support, best_score
# -----------------------
# RAG retrieval + composition
# -----------------------
def retrieve_sentences(question: str, text: str, k: int = 3, verbose=False) -> Tuple[List[str], float]:
    qs = tokenize(lemma_or_lower(question))
    sents = split_sentences(text)
    scored = []
    for s in sents:
        sim = jaccard(qs, tokenize(lemma_or_lower(s)))
        scored.append((sim, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for sim, s in scored[:k] if sim > 0]
    best_sim = scored[0][0] if scored else 0.0
    if verbose:
        print(f"RAG: best_sim={best_sim:.3f}")
        for sim, s in scored[:3]:
            print(f"  sim={sim:.3f} :: {s[:140]}")
    return top, best_sim

def compose_answer_from_snippets(question: str, snippets: List[str], triples: List[Dict],
                                 use_ollama: bool, model: str, verbose=False) -> str:
    if use_ollama and HAVE_OLLAMA:
        context = ""
        if triples:
            tri_lines = [f"- {t['head_entity']['entity']} {t['relation']['relation']} {t['tail_entity']['entity']}"
                         for t in triples[:5]]
            context += "Triples:\n" + "\n".join(tri_lines) + "\n"
        if snippets:
            context += "Snippets:\n" + "\n".join(f"- {s}" for s in snippets)
        sys_prompt = ("Answer ONLY using the provided Triples and Snippets. "
                      "If insufficient information is present, reply exactly: "
                      "'I don't know from the given document.' Keep answers concise.")
        user_msg = f"Question: {question}\n\n{context}"
        resp = ollama.chat(
            model=model,
            messages=[{"role":"system","content":sys_prompt},
                      {"role":"user","content":user_msg}],
            options={"temperature":0.0, "num_predict":256}
        )
        return (resp.get("message",{}) or {}).get("content","").strip()

    # non-LLM: just return snippets or refuse
    return " ".join(snippets) if snippets else "I don't know from the given document."

# -----------------------
# Main
# -----------------------
def main():
    ap = argparse.ArgumentParser(description="QA over doc via KG-first + RAG fallback w/ thresholds.")
    ap.add_argument("--doc", required=True, help="Path to the original .txt document.")
    ap.add_argument("--triples", required=True, help="Path to triples JSON (universal or ollama).")
    ap.add_argument("--ask", required=True, help="Your natural-language question.")
    ap.add_argument("--use_ollama", action="store_true", help="Use Ollama to compose final answers (optional).")
    ap.add_argument("--model", default="llama3.2", help="Ollama model if --use_ollama.")
    ap.add_argument("--verbose", action="store_true", help="Print scoring diagnostics.")
    args = ap.parse_args()

    text = load_text(args.doc)
    triples = load_triples(args.triples)

    if args.verbose:
        print(f"Q: {args.ask}")
        print(f"Triples loaded: {len(triples)}")

    # 1) KG-first
    kg_answer, used_triples, kg_score = answer_from_triples(args.ask, triples, verbose=args.verbose)

    # 2) RAG retrieval (always compute; may be used to augment or fallback)
    snippets, best_sim = retrieve_sentences(args.ask, text, k=3, verbose=args.verbose)

    # Decision
    if kg_answer:
        final = kg_answer
        # Optionally let an LLM compose final short answer from both signals
        if args.use_ollama and HAVE_OLLAMA:
            final = compose_answer_from_snippets(args.ask, snippets, used_triples, True, args.model, verbose=args.verbose)
        else:
            # attach context only if it looks relevant
            if best_sim >= MIN_RAG_SIM and snippets:
                final += "  (Context: " + " | ".join(snippets) + ")"
    else:
        # KG failed; consider RAG
        if best_sim < MIN_RAG_SIM:
            final = "I don't know from the given document."
        else:
            final = compose_answer_from_snippets(args.ask, snippets, triples, args.use_ollama and HAVE_OLLAMA, args.model, verbose=args.verbose)
    target = is_entity_def_question(args.ask)
    if target and snippets:
        # For definition-style questions, prefer the best snippet directly,
        # or summarize with Ollama if enabled.
        if args.use_ollama and HAVE_OLLAMA:
            final = compose_answer_from_snippets(args.ask, snippets[:2], [], True, args.model)
        else:
            final = snippets[0]
        print("\n=== ANSWER ===")
        print(final)
        if args.verbose:
            print("\n(Def-style; answered from snippet)")
        return


if __name__ == "__main__":
    main()

"""
# Examples:

# (A) Fast, no LLM
python -X utf8 qa_anydoc_v2.py ^
  --doc .\input\complex_demo.txt ^
  --triples .\output\complex_llm_triples.json ^
  --ask "Who does Priya Raman report to?" ^
  --verbose

# (B) With Ollama composing final answer
python -X utf8 qa_anydoc_v2.py ^
  --doc .\input\complex_demo.txt ^
  --triples .\output\complex_llm_triples.json ^
  --ask "Where are the R&D labs located?" ^
  --use_ollama --model llama3.2 ^
  --verbose

# Irrelevant question behavior
python -X utf8 qa_anydoc_v2.py ^
  --doc .\input\complex_demo.txt ^
  --triples .\output\complex_llm_triples.json ^
  --ask "When is the iPhone 21 releasing?" ^
  --verbose
"""
