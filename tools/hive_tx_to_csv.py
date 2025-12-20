"""Utility to export Hive account monetary operations to CSV.

The script pulls account history from a public Hive node and writes a CSV file
with a simplified view of transfers, rewards, and power up/down events.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import urllib.request
import urllib.error
import json
import time

API_NODES = [
    "https://api.hive.blog",
    "https://api.deathwing.me",
]

SUPPORTED_OPS = {
    "transfer",
    "interest",
    "fill_vesting_withdraw",
    "curation_reward",
    "producer_reward",
    "author_reward",
    "comment_benefactor_reward",
    "fill_order",
    "fill_convert_request",
    "convert",
    "proposal_pay",
    "transfer_to_vesting",
    "delegate_vesting_shares",
    "return_vesting_delegation",
}


class HiveAPIError(RuntimeError):
    """Raised when the Hive API repeatedly fails."""


class HiveAPI:
    def __init__(self, nodes: Iterable[str], retries: int = 3, backoff: float = 1.0) -> None:
        self.nodes = list(nodes)
        self.retries = retries
        self.backoff = backoff
        self._node_index = 0

    def _request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        last_error: Optional[Exception] = None
        for attempt in range(self.retries * len(self.nodes)):
            node = self.nodes[self._node_index]
            self._node_index = (self._node_index + 1) % len(self.nodes)
            req = urllib.request.Request(
                node,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception as exc:  # noqa: BLE001 - retry generic network errors
                last_error = exc
                time.sleep(self.backoff)
        raise HiveAPIError(f"Hive API request failed after retries: {last_error}")

    def get_account_history(self, account: str, start: int, limit: int) -> List[Any]:
        payload = {
            "jsonrpc": "2.0",
            "method": "condenser_api.get_account_history",
            "params": [account, start, limit],
            "id": 1,
        }
        result = self._request(payload)
        return result.get("result", [])

    def get_dynamic_global_properties(self) -> Dict[str, Any]:
        payload = {"jsonrpc": "2.0", "method": "condenser_api.get_dynamic_global_properties", "params": [], "id": 1}
        result = self._request(payload)
        return result.get("result", {})


def vests_to_hp(vests: float, global_props: Dict[str, Any]) -> float:
    total_vesting_fund_hive = float(global_props["total_vesting_fund_hive"].split()[0])
    total_vesting_shares = float(global_props["total_vesting_shares"].split()[0])
    ratio = total_vesting_fund_hive / total_vesting_shares
    return round(vests * ratio, 3)


def parse_amount(amount: str) -> Tuple[float, str]:
    quantity, symbol = amount.split()
    return float(quantity), symbol


def classify_operation(op_type: str, op_body: Dict[str, Any], account: str, global_props: Dict[str, Any]):
    currency: Optional[str] = None
    amount: Optional[float] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    direction: Optional[str] = None

    if op_type == "transfer":
        amount, currency = parse_amount(op_body["amount"])
        sender, recipient = op_body["from"], op_body["to"]
        direction = "incoming" if recipient == account else "outgoing"
    elif op_type == "interest":
        amount, currency = parse_amount(op_body["interest"])
        sender, recipient = "hive.rewards", op_body["owner"]
        direction = "incoming"
    elif op_type == "fill_vesting_withdraw":
        amount, currency = parse_amount(op_body["deposited"])
        sender, recipient = "staked.hive", op_body["to_account"]
        direction = "unstake"
    elif op_type == "curation_reward":
        amount = vests_to_hp(float(op_body["reward"].split()[0]), global_props)
        currency = "HP"
        sender, recipient = "hive.rewards", op_body["curator"]
        direction = "incoming"
    elif op_type == "producer_reward":
        amount = vests_to_hp(float(op_body["vesting_shares"].split()[0]), global_props)
        currency = "HP"
        sender, recipient = "hive.rewards", op_body["producer"]
        direction = "incoming"
    elif op_type == "author_reward":
        rows = []
        if float(op_body["hbd_payout"].split()[0]) > 0:
            rows.append(("incoming", "hive.rewards", op_body["author"], "HBD", float(op_body["hbd_payout"].split()[0])))
        if float(op_body["hive_payout"].split()[0]) > 0:
            rows.append(("incoming", "hive.rewards", op_body["author"], "HIVE", float(op_body["hive_payout"].split()[0])))
        vests = float(op_body["vesting_payout"].split()[0])
        if vests > 0:
            rows.append(("incoming", "hive.rewards", op_body["author"], "HP", vests_to_hp(vests, global_props)))
        return rows
    elif op_type == "comment_benefactor_reward":
        rows = []
        if float(op_body["hbd_payout"].split()[0]) > 0:
            rows.append(("incoming", "hive.rewards", op_body["benefactor"], "HBD", float(op_body["hbd_payout"].split()[0])))
        if float(op_body["hive_payout"].split()[0]) > 0:
            rows.append(("incoming", "hive.rewards", op_body["benefactor"], "HIVE", float(op_body["hive_payout"].split()[0])))
        vests = float(op_body["vesting_payout"].split()[0])
        if vests > 0:
            rows.append(("incoming", "hive.rewards", op_body["benefactor"], "HP", vests_to_hp(vests, global_props)))
        return rows
    elif op_type == "fill_order":
        current_amount, current_symbol = parse_amount(op_body["current_pays"])
        open_amount, open_symbol = parse_amount(op_body["open_pays"])
        rows = []
        if op_body["current_owner"] == account:
            rows.append(("outgoing", op_body["current_owner"], "hive.market", current_symbol, current_amount))
            rows.append(("incoming", "hive.market", op_body["current_owner"], open_symbol, open_amount))
        elif op_body["open_owner"] == account:
            rows.append(("incoming", "hive.market", op_body["open_owner"], current_symbol, current_amount))
            rows.append(("outgoing", op_body["open_owner"], "hive.market", open_symbol, open_amount))
        return rows
    elif op_type == "fill_convert_request":
        amount, currency = parse_amount(op_body["amount_out"])
        sender, recipient = op_body["owner"], op_body["requestid"]
        direction = "incoming"
    elif op_type == "convert":
        amount, currency = parse_amount(op_body["amount"])
        sender, recipient = op_body["owner"], op_body["requestid"]
        direction = "outgoing"
    elif op_type == "proposal_pay":
        amount, currency = parse_amount(op_body["payment"])
        sender, recipient = op_body["payer"], op_body["receiver"]
        direction = "incoming"
    elif op_type == "transfer_to_vesting":
        amount, currency = parse_amount(op_body["amount"])
        sender, recipient = op_body["from"], "staked.hive"
        direction = "stake"
    elif op_type == "delegate_vesting_shares":
        amount = vests_to_hp(float(op_body["vesting_shares"].split()[0]), global_props)
        currency = "HP"
        sender, recipient = op_body["delegator"], op_body["delegatee"]
        direction = "delegate"
    elif op_type == "return_vesting_delegation":
        amount = vests_to_hp(float(op_body["vesting_shares"].split()[0]), global_props)
        currency = "HP"
        sender, recipient = op_body["account"], op_body["account"]
        direction = "undelegate"

    if currency is None or amount is None:
        return []
    return [(direction or "", sender or "", recipient or "", currency, amount)]


def collect_transactions(api: HiveAPI, account: str, start: datetime, end: datetime) -> List[Tuple]:
    transactions: List[Tuple] = []
    # get last index
    last_history = api.get_account_history(account, -1, 1)
    if not last_history:
        return transactions
    last_index = last_history[-1][0]

    current_start = last_index
    batch = 1000
    global_props = api.get_dynamic_global_properties()

    while current_start >= 0:
        history = api.get_account_history(account, current_start, batch)
        if not history:
            break
        for _, entry in history:
            op_type, op_body = entry["op"]
            if op_type not in SUPPORTED_OPS:
                continue
            op_time = datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            if op_time < start:
                return transactions
            if op_time > end:
                continue
            rows = classify_operation(op_type, op_body, account, global_props)
            for direction, sender, recipient, currency, amount in rows:
                transactions.append((op_time.isoformat(), op_type, direction, sender, recipient, currency, amount))
        current_start = history[0][0] - 1
    return list(reversed(transactions))


def write_csv(path: str, rows: List[Tuple]) -> None:
    headers = ["timestamp", "type", "direction", "sender", "recipient", "currency", "amount"]
    with open(path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Hive account transactions to CSV")
    parser.add_argument("accounts", nargs="+", help="One or more Hive account names")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD, inclusive)")
    parser.add_argument("--output", default="hive_transactions.csv", help="Output CSV path")
    parser.add_argument("--node", action="append", help="Additional Hive API node URL")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    nodes = API_NODES + (args.node or [])
    api = HiveAPI(nodes=nodes)

    start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(args.end, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)

    all_rows: List[Tuple] = []
    for account in args.accounts:
        rows = collect_transactions(api, account, start, end)
        labelled = [(row[0], row[1], row[2], row[3], row[4], row[5], row[6], account) for row in rows]
        all_rows.extend(labelled)

    if all_rows:
        # add account column header
        headers = ["timestamp", "type", "direction", "sender", "recipient", "currency", "amount", "account"]
        with open(args.output, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(all_rows)
        print(f"Wrote {len(all_rows)} rows to {args.output}")
    else:
        print("No matching transactions found for the provided date range.")


if __name__ == "__main__":
    main()
