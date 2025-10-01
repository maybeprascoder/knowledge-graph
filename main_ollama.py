# main_ollama.py
# Text → triples via a local LLM (Ollama). Outputs JSON/CSV + optional HTML (PyVis).
# Usage:
#   python -X utf8 main_ollama.py --inputpath .\input\mydoc.txt --outlabel mydoc_llm --model llama3.1:8b --html
#   python -X utf8 main_ollama.py --inputpath .\input\ --outlabel alldocs_llm --model mistral --html

import argparse, os, sys, json, glob, pickle, re, time
from csv import DictWriter
from typing import List, Dict
import networkx as nx

# Optional HTML viz
try:
    from pyvis.network import Network
    HAVE_PYVIS = True
except Exception:
    HAVE_PYVIS = False

# ---- CLI
p = argparse.ArgumentParser(description="Extract knowledge-graph triples via Ollama (local LLM).")
p.add_argument("--inputpath", required=True, help="Path to .txt file OR a folder OR a glob (e.g., ./input/*.txt)")
p.add_argument("--outlabel", required=True, help="Prefix for outputs in ./output/")
p.add_argument("--model", default="llama3.1:8b", help="Ollama model name (e.g., llama3.1:8b, mistral, phi3)")
p.add_argument("--max_chars", type=int, default=1800, help="Chunk size in characters per LLM call")
p.add_argument("--html", action="store_true", help="Write HTML graph if edges>0 (requires pyvis)")
p.add_argument("--min_edges", type=int, default=0, help="HTML only if edges>=min_edges")
p.add_argument("--retry", type=int, default=2, help="Retries per chunk on JSON parse failure")
args = p.parse_args()

out_prefix = f"./output/{args.outlabel}"
os.makedirs("./output", exist_ok=True)

# ---- IO helpers
def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def list_docs(inputpath: str) -> List[str]:
    if os.path.isdir(inputpath):
        files = glob.glob(os.path.join(inputpath, "*.txt"))
    elif any(ch in inputpath for ch in "*?[]"):
        files = glob.glob(inputpath)
    else:
        files = [inputpath]
    files = [f for f in files if f.lower().endswith(".txt")]
    files.sort()
    return files

def save_pickle(obj, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(obj, f)

def save_json(obj, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def save_csv(rows: List[Dict], path: str, fieldnames: List[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

# ---- LLM (Ollama)
try:
    import ollama
except Exception as e:
    print("ERROR: ollama package not available. Install Ollama desktop/daemon and `pip install ollama`.", file=sys.stderr)
    sys.exit(2)
SYSTEM_PROMPT = """You convert text into a JSON array of knowledge-graph triples.
Each triple has: head_entity, relation, tail_entity.
Return ONLY valid JSON (no extra prose, no code fences, no trailing commas).
Output must be a JSON array (e.g., [] or [ { ... }, ... ]).
For each triple use this schema:
{
  "head_entity": {"entity": "<text>", "attribute": "<optional type>"},
  "relation":    {"relation": "<verb_or_relation>"},
  "tail_entity": {"entity": "<text>", "attribute": "<optional type>"}
}
Guidelines:
- Prefer concise head/tail (no determiners like 'the', 'a').
- Use lowercase relation lemmas (e.g., 'works_at', 'reports_to', 'located_in').
- Merge trivial facts; ignore fluff. If no triples, return [].
"""

def chunk_text(s: str, max_chars: int):
    s = s.strip()
    if len(s) <= max_chars:
        return [s]
    chunks = []
    start = 0
    while start < len(s):
        end = min(len(s), start + max_chars)
        # try to break at sentence end
        dot = s.rfind(".", start, end)
        cut = dot+1 if dot != -1 and dot > start + 0.5*max_chars else end
        chunks.append(s[start:cut].strip())
        start = cut
    return [c for c in chunks if c]

JSON_SNIP = re.compile(r"\[.*\]", re.DOTALL)

def repair_json_like(s: str) -> str:
    # strip fences
    s = s.strip().replace("```json", "").replace("```", "")
    # keep only the JSON-ish array if present
    m = JSON_SNIP.search(s)
    if m:
        s = m.group(0)
    # remove trailing commas before ] or }
    s = re.sub(r",\s*([\]\}])", r"\1", s)
    # normalize quotes if the model used single quotes
    # (only if it looks like JSON objects but with single quotes)
    if "'" in s and '"' not in s[:200]:
        s = re.sub(r"'", '"', s)
    # ensure it's an array (some models return one object)
    st = s.strip()
    if not st.startswith("["):
        s = "[" + st + "]"
    return s

def call_ollama(model: str, content: str, retry: int):
    last_err = None
    for attempt in range(retry + 1):
        try:
            resp = ollama.chat(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": content}
                ],
                options={"temperature": 0.0}  # make output more deterministic
            )
            raw = (resp.get("message", {}) or {}).get("content", "").strip()
            s = repair_json_like(raw)
            data = json.loads(s)
            if isinstance(data, dict):
                data = data.get("triples", [])
            if isinstance(data, list):
                return data
        except Exception as e:
            last_err = e
            time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"Ollama parse failed after {retry+1} tries: {last_err}")

def clean_np(t: str) -> str:
    t = t.strip().strip("\"'.,:;!?()[]{}").lower()
    words = t.split()
    if words and words[0] in {"a","an","the"}:
        words = words[1:]
    return " ".join(words)

def normalize_triple(t: Dict) -> Dict:
    h = clean_np(t.get("head_entity", {}).get("entity", ""))
    r = t.get("relation", {}).get("relation", "").strip().lower().replace(" ", "_")
    o = clean_np(t.get("tail_entity", {}).get("entity", ""))
    if not (h and r and o):
        return None
    return {
        "head_entity": {"entity": h, "attribute": t.get("head_entity", {}).get("attribute", "")},
        "relation":    {"relation": r},
        "tail_entity": {"entity": o, "attribute": t.get("tail_entity", {}).get("attribute", "")},
    }

def dedupe(triples: List[Dict]) -> List[Dict]:
    seen, out = set(), []
    for t in triples:
        key = (t["head_entity"]["entity"], t["relation"]["relation"], t["tail_entity"]["entity"])
        if key not in seen:
            seen.add(key); out.append(t)
    return out

# ---- Process
files = list_docs(args.inputpath)
if not files:
    print("No .txt files found. Provide a file, folder, or glob.", file=sys.stderr)
    sys.exit(2)

all_triples: List[Dict] = []
for path in files:
    text = read_text(path)
    parts = chunk_text(text, args.max_chars)
    for i, chunk in enumerate(parts, 1):
        triples = call_ollama(args.model, chunk, args.retry)
        for t in triples:
            nt = normalize_triple(t)
            if nt: all_triples.append(nt)

all_triples = dedupe(all_triples)
print(f"Total LLM triples: {len(all_triples)} from {len(files)} docs")

# ---- Save triples
triples_pkl  = f"{out_prefix}_triples.pkl"
triples_json = f"{out_prefix}_triples.json"
triples_csv  = f"{out_prefix}_triples.csv"

save_pickle(all_triples, triples_pkl)
save_json(all_triples, triples_json)
save_csv(
    [{"head":t["head_entity"]["entity"],
      "head_attr":t["head_entity"]["attribute"],
      "relation":t["relation"]["relation"],
      "tail":t["tail_entity"]["entity"],
      "tail_attr":t["tail_entity"]["attribute"]} for t in all_triples],
    triples_csv,
    fieldnames=["head","head_attr","relation","tail","tail_attr"]
)
print(f"Saved: {triples_pkl}, {triples_json}, {triples_csv}")

# ---- Graph + HTML
G = nx.MultiDiGraph()
for t in all_triples:
    h = t["head_entity"]["entity"]; r = t["relation"]["relation"]; o = t["tail_entity"]["entity"]
    G.add_node(h, attr=t["head_entity"]["attribute"])
    G.add_node(o, attr=t["tail_entity"]["attribute"])
    G.add_edge(h, o, relation=r)

graph_pkl = f"{out_prefix}_nx_graph.pkl"
with open(graph_pkl, "wb") as f:
    pickle.dump(G, f)
print(f"Saved graph: {graph_pkl} (nodes={G.number_of_nodes()}, edges={G.number_of_edges()})")

if args.html and HAVE_PYVIS and G.number_of_edges() >= args.min_edges:
    net = Network(height="100vh", width="100%", notebook=False)
    net.set_edge_smooth("dynamic"); net.toggle_physics(True); net.from_nx(G)
    for e in net.edges: e["label"] = e["relation"]
    html_path = f"{out_prefix}_graph.html"
    net.write_html(html_path, open_browser=False, notebook=False)  # avoids template bug
    print(f"Graph HTML: {html_path}")
elif args.html and not HAVE_PYVIS:
    print("PyVis not installed. Run: pip install pyvis")
elif G.number_of_edges() < args.min_edges:
    print(f"Graph has fewer than --min_edges ({args.min_edges}); HTML skipped.")
