"""
Escrova Arbitration Agent
Monitors EscrovaVault on Celo. Resolves disputes. Earns 1% fees.
Runs every 5 minutes.
"""

import schedule
import time
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

load_dotenv()

from tools import (
    scan_all_escrows,
    get_disputed_escrows_tool,
    arbitrate_dispute,
    check_delivery_content,
    check_agent_earnings,
    send_telegram_update,
    moonpay_get_swap_quote,
)
from config import GEMINI_API_KEY, MONITOR_INTERVAL_MINUTES

# -- LLM ----
# Using Google Gemini for cost-effectiveness
llm = ChatGoogleGenerativeAI(
    api_key=GEMINI_API_KEY,
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=2000,
)

# -- Agent --
agent = create_react_agent(llm, [
    scan_all_escrows,
    get_disputed_escrows_tool,
    arbitrate_dispute,
    check_delivery_content,
    check_agent_earnings,
    send_telegram_update,
    moonpay_get_swap_quote,
])

SYSTEM = """You are Escrova - an autonomous AI arbitration agent on Celo.

Your responsibilities:
1. Monitor the EscrovaVault contract for disputes and overdue escrows
2. When a dispute exists: fetch the criteria + delivery, evaluate fairly, resolve on-chain
3. Your ruling is FINAL and executed as a real blockchain transaction
4. Earn 1% platform fees from every resolved escrow - you are self-sustaining

Arbitration principles:
- Read the criteria carefully - it defines what was promised
- Check the delivery hash - does it actually match the criteria?
- When in doubt, ask: "Would a reasonable person consider this criteria satisfied?"
- If delivery is missing or clearly incomplete -> buyer wins
- If delivery exists and substantially meets criteria -> seller wins
- Record your reasoning clearly - it is stored permanently on-chain

Be fair, be fast, be final. You are the trust layer."""


def run_monitor_cycle():
    print(f"\n{'='*50}")
    print("Escrova monitoring cycle...")

    try:
        result = agent.invoke({"messages": [HumanMessage(content=f"""
{SYSTEM}

Run your monitoring cycle:
1. Scan all escrows - report counts by status
2. Check for any DISPUTED escrows
3. For each dispute: evaluate criteria vs delivery, make a ruling, execute resolveDispute on-chain
4. Check your cUSD earnings from platform fees
5. Send a Telegram summary (mention any disputes resolved, current fee earnings)
6. If nothing to do, just report the current state briefly
""")]})

        for msg in result["messages"]:
            if hasattr(msg, "content") and msg.content:
                print(f"[Agent]: {msg.content}")

    except Exception as e:
        print(f"[ERROR] {e}")
        import requests
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": f"[Escrova] Error: {str(e)[:200]}"},
                timeout=5
            )
        except:
            pass


def main():
    print("Escrova starting...")
    print(f"Contract: {os.environ.get('ESCROVA_CONTRACT_ADDRESS', 'NOT SET')}")
    print(f"Agent wallet: {os.environ.get('AGENT_WALLET_ADDRESS', 'NOT SET')}")
    print(f"Chain: {'Alfajores testnet' if os.environ.get('USE_TESTNET') == 'true' else 'Celo mainnet'}")

    run_monitor_cycle()

    schedule.every(MONITOR_INTERVAL_MINUTES).minutes.do(run_monitor_cycle)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
