"""
balance.py — Running balance computation for transactions.
"""

from config import logger


def compute_running_balances(transactions: list) -> list:
    """
    Sort transactions by date and compute running_balance for each.

    Rules (from PRD):
    1. Sort all transactions by date ascending.
    2. Starting balance = 0 unless first record has type='starting' (use its amount).
    3. Each subsequent: running_balance = previous_balance + amount.
    4. Always overwrite any input running_balance value.
    """
    if not transactions:
        return transactions

    # Sort by date, then by type (starting first)
    def sort_key(t):
        type_order = 0 if t.get("type") == "starting" else 1
        return (t.get("date", ""), type_order)

    sorted_txns = sorted(transactions, key=sort_key)

    balance = 0.0

    for i, txn in enumerate(sorted_txns):
        if i == 0 and txn.get("type") == "starting":
            balance = float(txn["amount"])
            txn["running_balance"] = balance
        else:
            balance += float(txn["amount"])
            txn["running_balance"] = round(balance, 2)

    logger.info(f"Computed running balances for {len(sorted_txns)} transactions "
                f"(final balance: {balance:.2f})")

    return sorted_txns
