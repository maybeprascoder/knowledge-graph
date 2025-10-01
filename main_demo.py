# main_demo.py
import argparse
import json
import os
import pickle
from tqdm import tqdm
import networkx as nx
from pyvis.network import Network
import spacy
import sys
import subprocess
from csv import DictWriter

# ---------------------------
# Args
# ---------------------------
parser = argparse.ArgumentParser(
    description="Build a simple knowledge graph from text using spaCy (no Ollama)."
)
parser.add_argument(
    "--inputpath",
    type=str,
    default="./input/metamorphosis-kafka.txt",
    help="Path to a UTF-8 text file to parse",
)
parser.add_argument(
    "--outlabel",
    type=str,
    required=True,
    help="Name used for output files (under ./output)",
)
args = parser.parse_args()
input_file = args.inputpath
out_label = args.outlabel

print(f"script called with input file: {input_file}, output label: {out_label}")

# ---------------------------
# IO helpers
# ---------------------------
def ensure_dir_for(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def save_pickle(obj, path: str):
    ensure_dir_for(path)
    with open(path, "wb") as f:
        pickle.dump(obj, f)

def save_json(obj, path: str):
    ensure_dir_for(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def save_csv(rows, path: str, fieldnames):
    ensure_dir_for(path)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

# ---------------------------
# Read text
# ---------------------------
with open(input_file, "r", encoding="utf-8") as f:
    full_content = f.read()
print(f"full content read from {input_file} => {full_content[:100]}...")

# ---------------------------
# spaCy model (auto-install if missing)
# ---------------------------
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("spaCy model 'en_core_web_sm' not found. Downloading...")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# ---------------------------
# Triple extraction (S–V–O)
# ---------------------------
def extract_triples_spacy(text: str):
    """
    Extract subject–verb–object triples using dependency tags.
    This is heuristic but works on generic prose (even with few named entities).
    """
    doc = nlp(text)
    triples = []
    for sent in doc.sents:
        for token in sent:  # search for verbs
            if token.pos_ == "VERB":
                subj = None
                obj = None
                for child in token.children:
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        subj = child
                    elif child.dep_ in ("dobj", "attr", "pobj", "dative", "oprd"):
                        obj = child
                if subj and obj:
                    # expand to full noun phrases
                    subj_span = " ".join(w.text for w in subj.subtree)
                    obj_span = " ".join(w.text for w in obj.subtree)
                    triples.append({
                        "head_entity": {"entity": subj_span, "attribute": subj.pos_},
                        "tail_entity": {"entity": obj_span,  "attribute": obj.pos_},
                        "relation":    {"relation": token.lemma_}
                    })
    return triples

# ---------------------------
# Run extraction
# ---------------------------
all_triples = extract_triples_spacy(full_content)
print(f"{len(all_triples)} triples found")

# ---------------------------
# Save triples (pickle + JSON + CSV)
# ---------------------------
out_dir = f"./output/{out_label}"
triples_pkl = f"{out_dir}_triples.pkl"
triples_json = f"{out_dir}_triples.json"
triples_csv = f"{out_dir}_triples.csv"

save_pickle(all_triples, triples_pkl)
save_json(all_triples, triples_json)
csv_rows = [{
    "head": t["head_entity"]["entity"],
    "head_attr": t["head_entity"]["attribute"],
    "relation": t["relation"]["relation"],
    "tail": t["tail_entity"]["entity"],
    "tail_attr": t["tail_entity"]["attribute"],
} for t in all_triples]
save_csv(csv_rows, triples_csv, fieldnames=["head","head_attr","relation","tail","tail_attr"])
print(f"Saved triples → {triples_pkl}, {triples_json}, {triples_csv}")

# ---------------------------
# Build graph
# ---------------------------
G = nx.MultiDiGraph()
for t in tqdm(all_triples):
    head = t["head_entity"]["entity"].lower()
    tail = t["tail_entity"]["entity"].lower()
    rel  = t["relation"]["relation"].lower()
    G.add_node(head, attr=t["head_entity"]["attribute"])
    G.add_node(tail, attr=t["tail_entity"]["attribute"])
    G.add_edge(head, tail, relation=rel)

graph_pkl = f"{out_dir}_nx_graph.pkl"
save_pickle(G, graph_pkl)
print(f"Saved NetworkX graph → {graph_pkl}")

# ---------------------------
# Visualize with PyVis (only if non-empty)
# ---------------------------
if G.number_of_edges() > 0:
    net = Network(height="100vh", width="100%", notebook=False)
    net.set_edge_smooth("dynamic")
    net.toggle_physics(True)
    net.from_nx(G)
    for edge in net.edges:
        edge["label"] = edge["relation"]

    html_path = f"{out_dir}_graph.html"
    # Use write_html instead of show() to avoid template/render bug
    net.write_html(html_path, open_browser=False, notebook=False)
    print(f"Graph written to {html_path} ✅")
else:
    print("⚠️ No triples extracted — skipping visualization.")

