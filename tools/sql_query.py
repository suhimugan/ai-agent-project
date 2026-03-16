import sqlite3
from config.settings import DB_PATH


def sql_query(question: str) -> dict:
    """
    Translates a natural language question into a safe SQL query.
    Only allows SELECT statements — no data modification possible.
    Returns a summarized result, not raw database dumps.
    """
    query = _build_query(question)

    if not query:
        return {
            "status": "no_query",
            "message": "Could not determine a suitable query for this question."
        }

    # Security: block any non-SELECT statements
    if not _is_safe_query(query):
        return {
            "status": "blocked",
            "message": "Only SELECT queries are permitted."
        }

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"status": "no_results", "message": "No matching records found."}

        # Convert rows to list of dicts
        results = [dict(row) for row in rows]

        # Security: cap results to avoid sending huge dumps to the API
        return {
            "status": "success",
            "query_used": query,
            "row_count": len(results),
            "results": results[:10]
        }

    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


def _is_safe_query(query: str) -> bool:
    """Only allows SELECT statements. Blocks INSERT, UPDATE, DELETE, DROP etc."""
    cleaned = query.strip().upper()
    return cleaned.startswith("SELECT")


def _build_query(question: str) -> str:
    """
    Maps natural language questions to safe SQL queries.
    In Step 8 we will replace this with Claude-generated SQL.
    """
    q = question.lower()

    if any(w in q for w in ["how many customers", "total customers", "number of customers"]):
        return "SELECT COUNT(*) as total_customers FROM customers"

    if any(w in q for w in ["pro plan", "pro customers"]):
        return "SELECT name, email, joined_date FROM customers WHERE plan = 'Pro'"

    if any(w in q for w in ["enterprise"]):
        return "SELECT name, email, joined_date FROM customers WHERE plan = 'Enterprise'"

    if any(w in q for w in ["starter"]):
        return "SELECT name, email, joined_date FROM customers WHERE plan = 'Starter'"

    if any(w in q for w in ["refunded", "refund orders"]):
        return """
            SELECT c.name, o.product, o.amount, o.order_date
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE o.status = 'refunded'
        """

    if any(w in q for w in ["open ticket", "open support", "unresolved"]):
        return """
            SELECT c.name, t.issue, t.created_date
            FROM support_tickets t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.status = 'open'
        """

    if any(w in q for w in ["all customers", "list customers", "show customers"]):
        return "SELECT name, email, plan, joined_date FROM customers"

    if any(w in q for w in ["revenue", "total revenue", "total sales"]):
        return """
            SELECT SUM(amount) as total_revenue
            FROM orders
            WHERE status = 'completed'
        """

    return ""