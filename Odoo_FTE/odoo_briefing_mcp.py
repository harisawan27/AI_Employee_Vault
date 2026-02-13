import xmlrpc.client
import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from vault root
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Read Odoo config from environment
url = os.getenv("ODOO_URL", "http://localhost:8069")
db = os.getenv("ODOO_DB", "odoo_fte")
username = os.getenv("ODOO_USER", "admin")
password = os.getenv("ODOO_PASSWORD", "admin")


def _connect():
    """Authenticate with Odoo and return (uid, models proxy)."""
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})
        if not uid:
            raise ConnectionError(f"Odoo authentication failed for user '{username}' on db '{db}'")
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        return uid, models
    except ConnectionRefusedError:
        raise ConnectionError(f"Cannot reach Odoo at {url} — is the server running?")
    except OSError as e:
        raise ConnectionError(f"Odoo connection error: {e}")


def get_weekly_revenue():
    """Fetch last week's posted invoice totals from Odoo."""
    uid, models = _connect()

    # Calculate date range for "Last Week"
    today = datetime.date.today()
    start_week = today - datetime.timedelta(days=today.weekday() + 7)
    end_week = start_week + datetime.timedelta(days=6)

    # Search Invoices (account.move) that are 'posted' and type 'out_invoice'
    invoice_ids = models.execute_kw(db, uid, password, 'account.move', 'search',
        [[['move_type', '=', 'out_invoice'],
          ['state', '=', 'posted'],
          ['invoice_date', '>=', str(start_week)],
          ['invoice_date', '<=', str(end_week)]]])

    # Read the totals
    invoices = models.execute_kw(db, uid, password, 'account.move', 'read',
        [invoice_ids], {'fields': ['name', 'amount_total', 'partner_id']})

    total_revenue = sum(inv['amount_total'] for inv in invoices)

    return {
        "period": f"{start_week} to {end_week}",
        "total_revenue": total_revenue,
        "transaction_count": len(invoices)
    }


if __name__ == "__main__":
    try:
        print(get_weekly_revenue())
    except ConnectionError as e:
        print(f"ERROR: {e}")
