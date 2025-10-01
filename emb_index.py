import os
import json
import pickle
from typing import List, Dict, Tuple

import faiss  # pip install faiss-cpu

from database import db
from ollama_service import ollama_service


OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
INDEX_PKL = os.path.join(OUT_DIR, "facts_index.pkl")
FACTS_JSON = os.path.join(OUT_DIR, "facts.json")
MAX = int(os.getenv("EMB_MAX_FACTS", "500"))  # limit per section for faster builds


def rows_to_fact_sentences() -> List[Dict]:
    """Collect canonical facts from the graph as short sentences with metadata."""
    facts: List[Dict] = []

    # Expenses with vendor and date
    exp_rows = db.execute_query(
        f"""
        MATCH (r:Report)-[:HAS_ENTRY]->(x:Expense)
        OPTIONAL MATCH (x)-[:PAID_TO]->(v:Vendor)
        RETURN r.id AS report_id,
               toFloat(x.amount) AS amount,
               coalesce(x.category, x.spend_category, x.type_name, x.type_code, 'Unknown') AS category,
               coalesce(v.name, x.vendor, 'Unknown') AS vendor,
               x.currency AS currency,
               x.transaction_date AS expense_date,
               x.id AS expense_id
        LIMIT {MAX}
        """
    )
    for r in exp_rows:
        sent = (
            f"Expense {r.get('expense_id')} on {r.get('expense_date')} "
            f"for {r.get('amount')} {r.get('currency')} in {r.get('category')} to {r.get('vendor')} "
            f"(report {r.get('report_id')})."
        )
        facts.append({"text": sent, "kind": "expense", "meta": r})

    # Approvals
    appr_rows = db.execute_query(
        f"""
        MATCH (r:Report)-[a:APPROVED_BY]->(u:Employee)
        RETURN r.id AS report_id, toFloat(a.step) AS step, a.step_name AS step_name,
               a.decision AS decision, a.at AS decided_at, u.id AS approver_id, u.name AS approver_name
        LIMIT {MAX}
        """
    )
    for r in appr_rows:
        sent = (
            f"Report {r.get('report_id')} approval step {r.get('step')} ({r.get('step_name')}) "
            f"by {r.get('approver_name')} ({r.get('approver_id')}) decision {r.get('decision')} at {r.get('decided_at')}."
        )
        facts.append({"text": sent, "kind": "approval", "meta": r})

    # Payments
    pay_rows = db.execute_query(
        f"""
        MATCH (r:Report)-[:SETTLED_BY]->(p:Payment)
        RETURN r.id AS report_id, p.id AS payment_id, p.method AS method, p.status AS status,
               p.payment_date AS payment_date, toFloat(p.total_amount) AS total_amount,
               toFloat(p.company_paid) AS company_paid, toFloat(p.employee_due) AS employee_due
        LIMIT {MAX}
        """
    )
    for r in pay_rows:
        sent = (
            f"Report {r.get('report_id')} settled by payment {r.get('payment_id')} "
            f"on {r.get('payment_date')} method {r.get('method')} status {r.get('status')} "
            f"total {r.get('total_amount')} company_paid {r.get('company_paid')} employee_due {r.get('employee_due')}."
        )
        facts.append({"text": sent, "kind": "payment", "meta": r})

    # Vendor totals (simple rollups)
    vend_rows = db.execute_query(
        f"""
        MATCH (x:Expense)-[:PAID_TO]->(v:Vendor)
        RETURN v.name AS vendor, sum(toFloat(x.amount)) AS spend
        ORDER BY spend DESC
        LIMIT {MAX}
        """
    )
    for r in vend_rows:
        sent = f"Vendor {r.get('vendor')} total spend {r.get('spend')}."
        facts.append({"text": sent, "kind": "vendor_total", "meta": r})

    return facts


def build_index():
    os.makedirs(OUT_DIR, exist_ok=True)
    facts = rows_to_fact_sentences()
    print(f"Collected {len(facts)} facts. Model={os.getenv('OLLAMA_EMBED_MODEL', 'nomic-embed-text')} (EMB_MAX_FACTS={MAX}).")
    texts = [f["text"] for f in facts]
    vectors = ollama_service.embed(texts)
    if not vectors:
        raise RuntimeError("Embedding failed; ensure Ollama is running and OLLAMA_EMBED_MODEL is available")

    dim = len(vectors[0])
    index = faiss.IndexFlatIP(dim)
    import numpy as np
    mat = np.array(vectors, dtype="float32")
    # Normalize for cosine similarity via inner-product
    faiss.normalize_L2(mat)
    index.add(mat)

    with open(INDEX_PKL, "wb") as f:
        pickle.dump({"index_type": "faiss_ip", "dim": dim, "count": len(texts)}, f)
    with open(FACTS_JSON, "w", encoding="utf-8") as f:
        json.dump(facts, f, ensure_ascii=False)

    print(f"Built index with {len(texts)} facts. Index meta -> {INDEX_PKL}, facts -> {FACTS_JSON}")


def search_facts(query: str, k: int = 50) -> List[Dict]:
    import numpy as np
    with open(FACTS_JSON, "r", encoding="utf-8") as f:
        facts = json.load(f)
    with open(INDEX_PKL, "rb") as f:
        meta = pickle.load(f)
    dim = meta["dim"]
    index = faiss.IndexFlatIP(dim)
    # Rebuild index quickly (acceptable for small data; for large, persist faiss separately)
    vectors = ollama_service.embed([f["text"] for f in facts])
    mat = np.array(vectors, dtype="float32")
    faiss.normalize_L2(mat)
    index.add(mat)
    qv = ollama_service.embed([query])[0]
    qv = np.array([qv], dtype="float32")
    faiss.normalize_L2(qv)
    scores, idxs = index.search(qv, k)
    idxs = idxs[0].tolist()
    return [facts[i] for i in idxs if i < len(facts)]


if __name__ == "__main__":
    build_index()


