import os, csv
from neo4j import GraphDatabase


NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

# Folder where entries.csv / reports.csv / approvals.csv / payments.csv live
# Defaults to the repository root; override with CONCUR_CSV_DIR env var
CSV_DIR = os.getenv("CONCUR_CSV_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))


def batched(iterator, batch_size):
    batch = []
    for item in iterator:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def to_float(value):
    try:
        return float(value) if value not in (None, "") else None
    except Exception:
        return None


def create_constraints(tx):
    tx.run("CREATE CONSTRAINT employee_id IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT report_id   IF NOT EXISTS FOR (r:Report)   REQUIRE r.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT expense_id  IF NOT EXISTS FOR (x:Expense)  REQUIRE x.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT vendor_name IF NOT EXISTS FOR (v:Vendor)   REQUIRE v.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT payment_id  IF NOT EXISTS FOR (p:Payment)  REQUIRE p.id IS UNIQUE")


def ingest_reports(session, path):
    upsert_reports = """
    UNWIND $rows AS row
    WITH row WHERE row.ID IS NOT NULL
    MERGE (r:Report {id: row.ID})
      SET r.uri = row.URI,
          r.name = row.Name,
          r.create_date = row.CreateDate,
          r.submit_date = row.SubmitDate,
          r.last_modified = row.LastModifiedDate,
          r.currency = row.CurrencyCode,
          r.total_txn = row.TotalTransactionAmountF,
          r.total_posted = row.TotalPostedAmountF,
          r.total_approved = row.TotalApprovedAmountF,
          r.amount_due_employee = row.AmountDueEmployeeF,
          r.approval_status = row.ApprovalStatus,
          r.approval_date = row.ApprovalDate,
          r.payment_status = row.PaymentStatus,
          r.paid_date = row.PaidDate;
    """

    link_submitter = """
    UNWIND $rows AS row
    WITH row WHERE row.OwnerLoginID IS NOT NULL AND row.ID IS NOT NULL
    MERGE (e:Employee {id: row.OwnerLoginID})
      SET e.name = row.OwnerName
    WITH e, row
    MATCH (r:Report {id: row.ID})
    MERGE (e)-[:SUBMITTED]->(r);
    """

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for chunk in batched(reader, BATCH_SIZE):
            rows = []
            for r in chunk:
                r["TotalTransactionAmountF"] = to_float(r.get("TotalTransactionAmount"))
                r["TotalPostedAmountF"] = to_float(r.get("TotalPostedAmount"))
                r["TotalApprovedAmountF"] = to_float(r.get("TotalApprovedAmount"))
                r["AmountDueEmployeeF"] = to_float(r.get("AmountDueEmployee"))
                rows.append(r)
            session.run(upsert_reports, rows=rows)
            session.run(link_submitter, rows=rows)


def ingest_entries(session, path):
    upsert_entries_and_link = """
    UNWIND $rows AS row
    WITH row WHERE row.ID IS NOT NULL
    MERGE (x:Expense {id: row.ID})
      SET x.transaction_date = row.TransactionDate,
          x.amount = row.TransactionAmountF,
          x.currency = row.TransactionCurrencyCode,
          x.exchange_rate = row.ExchangeRateF,
          x.posted_amount = row.PostedAmountF,
          x.type_code = row.ExpenseTypeCode,
          x.type_name = row.ExpenseTypeName,
          x.description = row.Description,
          x.spend_category = row.SpendCategoryCode,
          x.location_country = row.LocationCountry,
          x.location_name = row.LocationName,
          x.payment_type_id = row.PaymentTypeID,
          x.is_personal = row.IsPersonal,
          x.is_billable = row.IsBillable
    WITH row
    MATCH (r:Report {id: row.ReportID})
    MATCH (x:Expense {id: row.ID})
    MERGE (r)-[:HAS_ENTRY]->(x);
    """

    link_vendor = """
    UNWIND $rows AS row
    WITH row WHERE row.ID IS NOT NULL AND trim(coalesce(row.VendorDescription, '')) <> ''
    MERGE (v:Vendor {name: row.VendorDescription})
    WITH row, v
    MATCH (x:Expense {id: row.ID})
    MERGE (x)-[:PAID_TO]->(v);
    """

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for chunk in batched(reader, BATCH_SIZE):
            rows = []
            for r in chunk:
                r["TransactionAmountF"] = to_float(r.get("TransactionAmount"))
                r["ExchangeRateF"] = to_float(r.get("ExchangeRate"))
                r["PostedAmountF"] = to_float(r.get("PostedAmount"))
                rows.append(r)
            session.run(upsert_entries_and_link, rows=rows)
            session.run(link_vendor, rows=rows)


def ingest_approvals(session, path):
    link_approvals = """
    UNWIND $rows AS row
    WITH row WHERE row.ReportID IS NOT NULL
    MERGE (approver:Employee {id: row.ApproverID})
      SET approver.name = row.ApproverName
    WITH row, approver
    MATCH (r:Report {id: row.ReportID})
    MERGE (r)-[a:APPROVED_BY {step: toFloat(row.StepOrder)}]->(approver)
      SET a.step_name = row.StepName,
          a.decision = row.Decision,
          a.at = row.DecisionTimestamp,
          a.comment = row.Comment;
    """

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for chunk in batched(reader, BATCH_SIZE):
            session.run(link_approvals, rows=list(chunk))


def ingest_payments(session, path):
    upsert_payments = """
    UNWIND $rows AS row
    WITH row WHERE row.PaymentID IS NOT NULL
    MERGE (p:Payment {id: row.PaymentID})
      SET p.method = row.PaymentMethod,
          p.payment_date = row.PaymentDate,
          p.total_amount = row.TotalAmountF,
          p.company_paid = row.CompanyPaidAmountF,
          p.employee_due = row.EmployeeDueAmountF,
          p.status = row.PaymentStatus;
    """

    link_payments = """
    UNWIND $rows AS row
    WITH row WHERE row.PaymentID IS NOT NULL AND row.ReportID IS NOT NULL
    MATCH (r:Report {id: row.ReportID})
    MATCH (p:Payment {id: row.PaymentID})
    MERGE (r)-[:SETTLED_BY]->(p);
    """

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for chunk in batched(reader, BATCH_SIZE):
            rows = []
            for r in chunk:
                r["TotalAmountF"] = to_float(r.get("TotalAmount"))
                r["CompanyPaidAmountF"] = to_float(r.get("CompanyPaidAmount"))
                r["EmployeeDueAmountF"] = to_float(r.get("EmployeeDueAmount"))
                rows.append(r)
            session.run(upsert_payments, rows=rows)
            session.run(link_payments, rows=rows)


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        session.execute_write(create_constraints)
        ingest_reports(session, os.path.join(CSV_DIR, "reports.csv"))
        ingest_entries(session, os.path.join(CSV_DIR, "entries.csv"))
        ingest_approvals(session, os.path.join(CSV_DIR, "approvals.csv"))
        ingest_payments(session, os.path.join(CSV_DIR, "payments.csv"))
    driver.close()
    print("Ingestion complete.")


if __name__ == "__main__":
    main()


