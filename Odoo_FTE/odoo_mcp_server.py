"""
WEBXES Tech — Odoo MCP Server (stdio)

Full MCP server exposing Odoo ERP data via JSON-RPC (xmlrpc).
7 tools: get_invoices, get_bills, get_payments, get_profit_and_loss,
         get_balance_sheet, create_invoice, get_weekly_revenue.

Wrapped with @retry + CircuitBreaker from retry_handler.py.

Usage:
    python Odoo_FTE/odoo_mcp_server.py   (stdio transport)
"""

import datetime
import json
import sys
import xmlrpc.client
from pathlib import Path

# Add vault root to path for imports
VAULT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VAULT_ROOT))

from config import ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD
from retry_handler import retry, CircuitBreaker

# Circuit breaker for Odoo
odoo_cb = CircuitBreaker("odoo", failure_threshold=5, recovery_timeout=300)


@retry(max_retries=3, base_delay=2.0, exceptions=(ConnectionError, xmlrpc.client.Fault, OSError))
def _connect():
    """Authenticate with Odoo and return (uid, models proxy)."""
    with odoo_cb:
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        if not uid:
            raise ConnectionError(f"Odoo auth failed for '{ODOO_USER}' on '{ODOO_DB}'")
        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
        return uid, models


def _execute(model, method, domain=None, fields=None, vals=None):
    """Execute an Odoo RPC call."""
    uid, models = _connect()
    if method == "search_read":
        return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, "search_read",
                                 [domain or []], {"fields": fields or []})
    elif method == "create":
        return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, "create", [vals or {}])
    elif method == "read":
        ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, "search", [domain or []])
        return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, "read",
                                 [ids], {"fields": fields or []})
    return []


# ── Tool implementations ──

def get_invoices(start_date: str = None, end_date: str = None) -> list:
    """Get customer invoices (out_invoice) within date range."""
    today = datetime.date.today()
    start = start_date or str(today - datetime.timedelta(days=30))
    end = end_date or str(today)
    domain = [
        ["move_type", "=", "out_invoice"],
        ["state", "=", "posted"],
        ["invoice_date", ">=", start],
        ["invoice_date", "<=", end],
    ]
    return _execute("account.move", "search_read", domain,
                    ["name", "partner_id", "amount_total", "invoice_date", "state"])


def get_bills(start_date: str = None, end_date: str = None) -> list:
    """Get vendor bills (in_invoice) within date range."""
    today = datetime.date.today()
    start = start_date or str(today - datetime.timedelta(days=30))
    end = end_date or str(today)
    domain = [
        ["move_type", "=", "in_invoice"],
        ["state", "=", "posted"],
        ["invoice_date", ">=", start],
        ["invoice_date", "<=", end],
    ]
    return _execute("account.move", "search_read", domain,
                    ["name", "partner_id", "amount_total", "invoice_date", "state"])


def get_payments(start_date: str = None, end_date: str = None) -> list:
    """Get payments within date range."""
    today = datetime.date.today()
    start = start_date or str(today - datetime.timedelta(days=30))
    end = end_date or str(today)
    domain = [
        ["date", ">=", start],
        ["date", "<=", end],
        ["state", "=", "posted"],
    ]
    return _execute("account.payment", "search_read", domain,
                    ["name", "partner_id", "amount", "date", "payment_type", "state"])


def get_profit_and_loss(start_date: str = None, end_date: str = None) -> dict:
    """Calculate P&L from journal entries (income vs. expense accounts)."""
    today = datetime.date.today()
    start = start_date or str(today.replace(day=1))
    end = end_date or str(today)

    # Income accounts (type = income, typically code starting with 4)
    income_domain = [
        ["date", ">=", start], ["date", "<=", end],
        ["account_id.account_type", "in", ["income", "income_other"]],
        ["parent_state", "=", "posted"],
    ]
    income_lines = _execute("account.move.line", "search_read", income_domain,
                            ["debit", "credit", "account_id"])
    total_income = sum(l.get("credit", 0) - l.get("debit", 0) for l in income_lines)

    # Expense accounts
    expense_domain = [
        ["date", ">=", start], ["date", "<=", end],
        ["account_id.account_type", "in", ["expense", "expense_direct_cost",
                                             "expense_depreciation"]],
        ["parent_state", "=", "posted"],
    ]
    expense_lines = _execute("account.move.line", "search_read", expense_domain,
                             ["debit", "credit", "account_id"])
    total_expense = sum(l.get("debit", 0) - l.get("credit", 0) for l in expense_lines)

    return {
        "period": f"{start} to {end}",
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_profit": round(total_income - total_expense, 2),
    }


def get_balance_sheet() -> dict:
    """Get current balance sheet summary (assets, liabilities, equity)."""
    today = str(datetime.date.today())

    def sum_lines(account_types):
        domain = [
            ["date", "<=", today],
            ["account_id.account_type", "in", account_types],
            ["parent_state", "=", "posted"],
        ]
        lines = _execute("account.move.line", "search_read", domain, ["debit", "credit"])
        return round(sum(l.get("debit", 0) - l.get("credit", 0) for l in lines), 2)

    assets = sum_lines(["asset_receivable", "asset_cash", "asset_current",
                        "asset_non_current", "asset_prepayments", "asset_fixed"])
    liabilities = -sum_lines(["liability_payable", "liability_current",
                               "liability_non_current", "liability_credit_card"])
    equity = -sum_lines(["equity", "equity_unaffected"])

    return {
        "as_of": today,
        "total_assets": assets,
        "total_liabilities": liabilities,
        "total_equity": equity,
    }


def create_invoice(partner_name: str, lines: list) -> dict:
    """Create a draft customer invoice.

    Args:
        partner_name: Customer name (must exist in Odoo).
        lines: List of {"product": str, "quantity": float, "price": float}.
    """
    uid, models = _connect()

    # Find partner
    partner_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, "res.partner", "search",
                                    [[["name", "ilike", partner_name]]], {"limit": 1})
    if not partner_ids:
        return {"error": f"Partner '{partner_name}' not found in Odoo"}

    invoice_lines = []
    for line in lines:
        invoice_lines.append((0, 0, {
            "name": line.get("product", "Service"),
            "quantity": line.get("quantity", 1),
            "price_unit": line.get("price", 0),
        }))

    invoice_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, "account.move", "create", [{
        "move_type": "out_invoice",
        "partner_id": partner_ids[0],
        "invoice_line_ids": invoice_lines,
    }])

    return {"invoice_id": invoice_id, "status": "draft", "partner": partner_name}


def get_weekly_revenue() -> dict:
    """Get last week's posted invoice totals."""
    today = datetime.date.today()
    start_week = today - datetime.timedelta(days=today.weekday() + 7)
    end_week = start_week + datetime.timedelta(days=6)
    invoices = get_invoices(str(start_week), str(end_week))
    total = sum(inv.get("amount_total", 0) for inv in invoices)
    return {
        "period": f"{start_week} to {end_week}",
        "total_revenue": total,
        "transaction_count": len(invoices),
    }


# ── MCP Server (stdio) ──

TOOLS = {
    "get_invoices": {
        "description": "Get customer invoices within a date range",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            },
        },
        "fn": get_invoices,
    },
    "get_bills": {
        "description": "Get vendor bills within a date range",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            },
        },
        "fn": get_bills,
    },
    "get_payments": {
        "description": "Get payments within a date range",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            },
        },
        "fn": get_payments,
    },
    "get_profit_and_loss": {
        "description": "Get profit & loss statement for a date range",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            },
        },
        "fn": get_profit_and_loss,
    },
    "get_balance_sheet": {
        "description": "Get current balance sheet summary",
        "inputSchema": {"type": "object", "properties": {}},
        "fn": get_balance_sheet,
    },
    "create_invoice": {
        "description": "Create a draft customer invoice",
        "inputSchema": {
            "type": "object",
            "properties": {
                "partner_name": {"type": "string", "description": "Customer name in Odoo"},
                "lines": {
                    "type": "array",
                    "description": "Invoice lines",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product": {"type": "string"},
                            "quantity": {"type": "number"},
                            "price": {"type": "number"},
                        },
                    },
                },
            },
            "required": ["partner_name", "lines"],
        },
        "fn": create_invoice,
    },
    "get_weekly_revenue": {
        "description": "Get last week's total invoice revenue",
        "inputSchema": {"type": "object", "properties": {}},
        "fn": get_weekly_revenue,
    },
}


def handle_request(request: dict) -> dict:
    """Handle a single JSON-RPC request."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "odoo-mcp", "version": "1.0.0"},
            },
        }

    if method == "notifications/initialized":
        return None  # no response for notifications

    if method == "tools/list":
        tools_list = []
        for name, spec in TOOLS.items():
            tools_list.append({
                "name": name,
                "description": spec["description"],
                "inputSchema": spec["inputSchema"],
            })
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}}

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        tool = TOOLS.get(tool_name)
        if not tool:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }
        try:
            result = tool["fn"](**arguments)
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, default=str)}],
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                    "isError": True,
                },
            }

    return {
        "jsonrpc": "2.0", "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


def main():
    """Run MCP server on stdio."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
