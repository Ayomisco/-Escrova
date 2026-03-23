# agent/tools.py
"""All tools available to the Escrova arbitration agent."""

import json
import time
import requests
from langchain.tools import tool
import contract as c
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ANTHROPIC_API_KEY


@tool
def scan_all_escrows() -> str:
    """
    Scan the EscrovaVault contract and return all escrows with their current status.
    Always call this first to understand the current state.
    Returns: list of all escrows with status, amount, criteria, deadline.
    """
    try:
        escrows = c.get_all_escrows()
        if not escrows:
            return json.dumps({"count": 0, "message": "No escrows found yet.", "escrows": []})
        summary = {
            "count": len(escrows),
            "by_status": {},
            "escrows": escrows,
        }
        for e in escrows:
            s = e["status"]
            summary["by_status"][s] = summary["by_status"].get(s, 0) + 1
        return json.dumps(summary, default=str)
    except Exception as ex:
        return json.dumps({"error": str(ex)})


@tool
def get_disputed_escrows_tool() -> str:
    """
    Get all escrows in DISPUTED state that require arbitration.
    These are the ones the agent must resolve.
    """
    try:
        disputed = c.get_disputed_escrows()
        if not disputed:
            return json.dumps({"message": "No disputes to resolve.", "disputed": []})
        return json.dumps({"count": len(disputed), "disputed": disputed}, default=str)
    except Exception as ex:
        return json.dumps({"error": str(ex)})


@tool
def arbitrate_dispute(escrow_id: int, seller_wins: bool, reasoning: str) -> str:
    """
    THE CORE ACTION: Resolve a disputed escrow as the arbiter.
    Call this ONLY after carefully analyzing:
      1. The work criteria (what was promised)
      2. The delivery hash (what was submitted)
      3. The dispute context

    seller_wins=True -> cUSD goes to seller (work accepted)
    seller_wins=False -> cUSD returns to buyer (work rejected)
    reasoning -> stored permanently on-chain and sent to both parties

    This executes a real on-chain transaction on Celo.
    """
    try:
        tx_hash = c.resolve_dispute_onchain(escrow_id, seller_wins, reasoning)
        result = {
            "success": True,
            "escrow_id": escrow_id,
            "verdict": "seller wins" if seller_wins else "buyer wins - refunded",
            "tx_hash": tx_hash,
            "celoscan_url": f"https://alfajores.celoscan.io/tx/{tx_hash}",
            "reasoning_onchain": reasoning,
            "message": f"Dispute resolved. TxHash: {tx_hash}"
        }
        return json.dumps(result)
    except Exception as ex:
        return json.dumps({"success": False, "error": str(ex)})


@tool
def check_delivery_content(delivery_hash: str, criteria: str) -> str:
    """
    Evaluate whether a delivery meets the escrow criteria.
    Fetches content from IPFS or URL and compares against criteria.
    Returns an assessment the agent can use to make its ruling.
    """
    try:
        content = ""
        if delivery_hash.startswith("Qm") or delivery_hash.startswith("bafy"):
            # IPFS hash
            resp = requests.get(f"https://ipfs.io/ipfs/{delivery_hash}", timeout=15)
            content = resp.text[:2000] if resp.status_code == 200 else f"Could not fetch IPFS: {resp.status_code}"
        elif delivery_hash.startswith("http"):
            resp = requests.get(delivery_hash, timeout=15)
            content = resp.text[:2000] if resp.status_code == 200 else f"Could not fetch URL: {resp.status_code}"
        else:
            content = f"Delivery reference: {delivery_hash}"

        return json.dumps({
            "delivery_hash": delivery_hash,
            "criteria": criteria,
            "content_preview": content,
            "assessment_needed": "Evaluate: does this delivery satisfy the criteria above?",
        })
    except Exception as ex:
        return json.dumps({"error": str(ex), "delivery_hash": delivery_hash})


@tool
def check_agent_earnings() -> str:
    """
    Check how much cUSD the Escrova agent has earned in 1% platform fees.
    The agent is economically self-sustaining - fees from escrows fund its operations.
    """
    try:
        balance = c.agent_cusd_balance()
        return json.dumps({
            "cusd_balance": balance,
            "message": f"Escrova agent has earned {balance:.4f} cUSD from platform fees.",
            "wallet": c.agent.address,
        })
    except Exception as ex:
        return json.dumps({"error": str(ex)})


@tool
def send_telegram_update(message: str) -> str:
    """
    Send a status update or alert to the human operator via Telegram.
    Use for: dispute resolutions, daily summaries, errors, new escrow alerts.
    """
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": f"[Escrova]\n\n{message}", "parse_mode": "HTML"},
            timeout=10
        )
        return json.dumps({"sent": resp.status_code == 200})
    except Exception as ex:
        return json.dumps({"sent": False, "error": str(ex)})


@tool
def moonpay_get_swap_quote(from_currency: str, to_currency: str, amount: float) -> str:
    """
    Get a swap quote from MoonPay CLI for cross-chain bridging.
    Useful when a buyer wants to deposit from another chain into Celo escrow.
    from_currency: e.g. "eth", "usdc", "matic"
    to_currency: e.g. "cusd", "celo"
    amount: amount in from_currency units
    """
    try:
        # MoonPay CLI is an MCP server - call it via HTTP
        resp = requests.get(
            "https://api.moonpay.com/v3/currencies/ask_price",
            params={
                "apiKey": MOONPAY_API_KEY,
                "baseCurrencyCode": from_currency,
                "quoteCurrencyCode": to_currency,
                "baseCurrencyAmount": amount,
            },
            timeout=10
        )
        data = resp.json()
        return json.dumps({
            "from": from_currency,
            "to": to_currency,
            "amount_in": amount,
            "quote": data,
            "message": f"MoonPay quote received for {amount} {from_currency} - {to_currency}"
        })
    except Exception as ex:
        return json.dumps({"error": str(ex)})
