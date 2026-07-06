"""Regenerate WORKED_EXAMPLES.md numbers by driving the real API.

Run after any math-affecting change and paste the printed request/response
blocks into WORKED_EXAMPLES.md — example numbers must be code output, never
hand-written (see CLAUDE.md iron rule #4).

Usage: python scripts/gen_worked_examples.py
"""

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from api.app import app  # noqa: E402

client = TestClient(app)

EXAMPLES = [
    (
        "ES swing long (§1256)",
        {
            "symbol": "ES",
            "side": "long",
            "entry": "5050.00",
            "account_equity": "25000.00",
            "leverage": "12",
            "pct_stop": "0.004",
            "risk_cash": "2500.00",
            "fees_open": "2.50",
            "fees_close": "2.50",
        },
        {
            "symbol": "ES",
            "side": "long",
            "entry": "5050.00",
            "target": "5100.00",
            "stop": "5029.75",
            "qty": 1,
            "fees_open": "2.50",
            "fees_close": "2.50",
            "slippage_open": "0.50",
            "slippage_close": "0.50",
            "energy_kwh": "0.2",
            "energy_cost_per_kwh": "0.14",
            "margin_loans": [{"loan_amount": "5000.00", "apr": "0.065", "days_held": 2}],
            "tax_mode": "1256",
            "st_rate": "0.24",
            "lt_rate": "0.15",
        },
    ),
    (
        "NQ intraday scalp short (short-term ordinary)",
        {
            "symbol": "NQ",
            "side": "short",
            "entry": "18500.00",
            "account_equity": "50000.00",
            "leverage": "8",
            "pct_stop": "0.003",
            "risk_cash": "1500.00",
            "fees_open": "3.00",
            "fees_close": "3.00",
        },
        {
            "symbol": "NQ",
            "side": "short",
            "entry": "18500.00",
            "target": "18450.00",
            "stop": "18555.50",
            "qty": 1,
            "fees_open": "3.00",
            "fees_close": "3.00",
            "slippage_open": "1.00",
            "slippage_close": "1.00",
            "energy_kwh": "0.05",
            "energy_cost_per_kwh": "0.14",
            "tax_mode": "short_term",
            "st_rate": "0.37",
        },
    ),
    (
        "CL energy trade long (§1256, margin loan)",
        {
            "symbol": "CL",
            "side": "long",
            "entry": "95.50",
            "account_equity": "15000.00",
            "leverage": "8",
            "pct_stop": "0.025",
            "risk_cash": "2500.00",
            "fees_open": "5.00",
            "fees_close": "5.00",
        },
        {
            "symbol": "CL",
            "side": "long",
            "entry": "95.50",
            "target": "100.00",
            "stop": "93.11",
            "qty": 1,
            "fees_open": "5.00",
            "fees_close": "5.00",
            "slippage_open": "2.00",
            "slippage_close": "2.00",
            "energy_kwh": "0.35",
            "energy_cost_per_kwh": "0.14",
            "margin_loans": [{"loan_amount": "3000.00", "apr": "0.070", "days_held": 1}],
            "tax_mode": "1256",
            "st_rate": "0.24",
            "lt_rate": "0.15",
        },
    ),
    (
        "GC macro long (§1256, 3 cascading loans)",
        {
            "symbol": "GC",
            "side": "long",
            "entry": "2050.00",
            "account_equity": "30000.00",
            "leverage": "7",
            "pct_stop": "0.02",
            "risk_cash": "4200.00",
            "fees_open": "4.00",
            "fees_close": "4.00",
        },
        {
            "symbol": "GC",
            "side": "long",
            "entry": "2050.00",
            "target": "2150.00",
            "stop": "2009.00",
            "qty": 1,
            "fees_open": "4.00",
            "fees_close": "4.00",
            "slippage_open": "1.00",
            "slippage_close": "1.00",
            "energy_kwh": "1.5",
            "energy_cost_per_kwh": "0.14",
            "margin_loans": [
                {"loan_amount": "10000.00", "apr": "0.065", "days_held": 5},
                {"loan_amount": "5000.00", "apr": "0.085", "days_held": 4},
                {"loan_amount": "2000.00", "apr": "0.120", "days_held": 2},
            ],
            "tax_mode": "1256",
            "st_rate": "0.24",
            "lt_rate": "0.15",
        },
    ),
]


def main() -> int:
    failures = 0
    for title, size_payload, pnl_payload in EXAMPLES:
        print(f"\n{'=' * 70}\n## {title}\n{'=' * 70}")
        for name, endpoint, payload in (
            ("SIZE", "/size", size_payload),
            ("PNL", "/pnl", pnl_payload),
        ):
            resp = client.post(endpoint, json=payload)
            print(f"--- {name} request ---")
            print(json.dumps(payload, indent=2))
            print(f"--- {name} response ({resp.status_code}) ---")
            print(json.dumps(resp.json(), indent=2))
            if resp.status_code != 200:
                failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
