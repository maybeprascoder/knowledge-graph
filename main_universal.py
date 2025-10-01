import argparse, os, sys, json, glob, pickle, subprocess, re
from csv import DictWriter
from typing import List, Dict
import spacy
import networkx as nx
from tqdm import tqdm

# Try PyVis (optional)
try:
    from pyvis.network import Network
    HAVE_PYVIS = True
except Exception:
    HAVE_PYVIS = False

# ---------------------------
# CLI
# ---------------------------
p = argparse.ArgumentParser(
    description="Universal text→triples→graph (spaCy). Pass a .txt file, a folder, or a glob."
)
p.add_argument("--inputpath", required=True,
               help="Path to a .txt file OR a folder OR a glob (e.g., ./input/*.txt)")
p.add_argument("--outlabel", required=True,
               help="Prefix for outputs in ./output/")
p.add_argument("--min_edges", type=int, default=0,
               help="Write HTML only if edges >= min_edges (default 0)")
p.add_argument("--max_docs", type=int, default=0,
               help="Process at most N docs (0 = no limit)")
p.add_argument("--html", action="store_true",
               help="Write interactive HTML graph (requires pyvis)")
p.add_argument("--drop_pronouns", action="store_true",
               help="Drop edges where head is a bare pronoun (he/she/it/they etc.)")
args = p.parse_args()

out_prefix = f"./output/{args.outlabel}"
os.makedirs("./output", exist_ok=True)

# ---------------------------
# spaCy model (auto-install)
# ---------------------------
def load_spacy():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        print("Downloading spaCy model 'en_core_web_sm' ...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        return spacy.load("en_core_web_sm")

nlp = load_spacy()

# ---------------------------
# Helpers: I/O
# ---------------------------
def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

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

# ---------------------------
# Helpers: text normalization
# ---------------------------
STOP_DETS = {"a","an","the"}
PRONOUNS  = {"he","she","it","they","him","her","them","his","its","their","we","us","i","me"}

def clean_np(text: str) -> str:
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    t = t.strip(" \t\n\r\"'.,:;!?()[]{}")
    words = t.split()
    if words and words[0].lower() in STOP_DETS:
        words = words[1:]
    return " ".join(words).lower()

def clean_rel(rel: str) -> str:
    return rel.strip().lower().replace(" ", "_")

def np_text(token):
    return " ".join(w.text for w in token.subtree)

# ---------------------------
# Triple extraction
# ---------------------------
PREP_MAP = {"in":"in","on":"on","at":"at","for":"for","to":"to","with":"with","into":"into","from":"from","of":"of"}

def add_triple(triples, subj, verb_lemma, obj):
    subj = clean_np(subj)
    obj  = clean_np(obj)
    if not subj or not obj:
        return
    if args.drop_pronouns and subj in PRONOUNS:
        return
    rel  = clean_rel(verb_lemma)
    triples.append({
        "head_entity": {"entity": subj, "attribute": "NP"},
        "relation":    {"relation": rel},
        "tail_entity": {"entity": obj,  "attribute": "NP"},
    })

def extract_svo_triples(doc):
    triples = []
    for sent in doc.sents:
        for v in sent:
            if v.pos_ != "VERB":
                continue
            verb = v.lemma_

            subjs = [c for c in v.children if c.dep_ in ("nsubj","nsubjpass")]
            objs  = [c for c in v.children if c.dep_ in ("dobj","attr","oprd")]

            # prepositional objects: VERB -> prep -> pobj
            prep_objs = []
            for prep in (c for c in v.children if c.dep_ == "prep"):
                # idiom: "in search of X" => search_for X
                pobj = next((x for x in prep.children if x.dep_ == "pobj"), None)
                if prep.lemma_ == "in" and pobj and pobj.lemma_ == "search":
                    of_prep = next((x for x in pobj.children if x.dep_ == "prep" and x.lemma_=="of"), None)
                    if of_prep:
                        of_pobj = next((x for x in of_prep.children if x.dep_=="pobj"), None)
                        if of_pobj:
                            prep_objs.append(("search_for", of_pobj))
                            continue  # skip generic "verb_in search"
                if pobj:
                    prep_norm = PREP_MAP.get(prep.lemma_, prep.lemma_)
                    prep_objs.append((f"{verb}_{prep_norm}", pobj))

            # coordinated objects (e.g., stones and pebbles)
            extra_objs = []
            for o in list(objs):
                for conj in (c for c in o.children if c.dep_ == "conj"):
                    extra_objs.append(conj)
            objs += extra_objs

            # coordinated subjects
            extra_subjs = []
            for s in list(subjs):
                for conj in (c for c in s.children if c.dep_ == "conj"):
                    extra_subjs.append(conj)
            subjs += extra_subjs

            # emit
            for s in subjs:
                s_txt = np_text(s)
                for o in objs:
                    add_triple(triples, s_txt, verb, np_text(o))
                for rel_prep, pobj in prep_objs:
                    add_triple(triples, s_txt, rel_prep, np_text(pobj))
    return triples

# Light NER templates
NER_REL_TEMPLATES = {
    ("PERSON","ORG"): "works_at",
    ("ORG","GPE"):    "located_in",
    ("PERSON","GPE"): "lives_in",
}

def extract_ner_pairs(doc):
    triples = []
    ents = list(doc.ents)
    for i in range(len(ents)):
        for j in range(i+1, len(ents)):
            a, b = ents[i], ents[j]
            key = (a.label_, b.label_)
            if key in NER_REL_TEMPLATES:
                triples.append({
                    "head_entity": {"entity": clean_np(a.text), "attribute": a.label_},
                    "relation":    {"relation": NER_REL_TEMPLATES[key]},
                    "tail_entity": {"entity": clean_np(b.text), "attribute": b.label_},
                })
    return triples

def dedupe_triples(triples):
    seen, out = set(), []
    for t in triples:
        key = (t["head_entity"]["entity"], t["relation"]["relation"], t["tail_entity"]["entity"])
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out

# ---------------------------
# Collect docs
# ---------------------------
def list_docs(inputpath: str) -> List[str]:
    if os.path.isdir(inputpath):
        files = glob.glob(os.path.join(inputpath, "*.txt"))
    elif any(ch in inputpath for ch in "*?[]"):
        files = glob.glob(inputpath)
    else:
        files = [inputpath]
    files = [f for f in files if f.lower().endswith(".txt")]
    files.sort()
    if args.max_docs and len(files) > args.max_docs:
        files = files[:args.max_docs]
    return files

files = list_docs(args.inputpath)
if not files:
    print("No .txt files found. Provide a file, folder, or glob.", file=sys.stderr)
    sys.exit(2)

# ---------------------------
# Process → merged triples/graph
# ---------------------------
all_triples = []
for path in tqdm(files, desc="Docs"):
    text = read_text(path)
    doc  = nlp(text)
    triples = extract_svo_triples(doc)
    triples += extract_ner_pairs(doc)
    all_triples.extend(triples)

all_triples = dedupe_triples(all_triples)
print(f"Total triples: {len(all_triples)} from {len(files)} docs")

# Save triples
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

# Build graph
G = nx.MultiDiGraph()
for t in all_triples:
    h = t["head_entity"]["entity"]
    r = t["relation"]["relation"]
    o = t["tail_entity"]["entity"]
    G.add_node(h, attr=t["head_entity"]["attribute"])
    G.add_node(o, attr=t["tail_entity"]["attribute"])
    G.add_edge(h, o, relation=r)

graph_pkl = f"{out_prefix}_nx_graph.pkl"
save_pickle(G, graph_pkl)
print(f"Saved graph: {graph_pkl} (nodes={G.number_of_nodes()}, edges={G.number_of_edges()})")

# HTML viz (optional)
if args.html and HAVE_PYVIS and G.number_of_edges() >= args.min_edges:
    net = Network(height="100vh", width="100%", notebook=False)
    net.set_edge_smooth("dynamic")
    net.toggle_physics(True)
    net.from_nx(G)
    for e in net.edges:  # add labels
        e["label"] = e["relation"]
    html_path = f"{out_prefix}_graph.html"
    # write_html avoids the Jinja template bug on Windows
    net.write_html(html_path, open_browser=False, notebook=False)
    print(f"Graph HTML: {html_path}")
elif args.html and not HAVE_PYVIS:
    print("PyVis not installed. Run: pip install pyvis")
elif G.number_of_edges() < args.min_edges:
    print(f"Graph has fewer than --min_edges ({args.min_edges}); HTML skipped.")