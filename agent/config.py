# agent/config.py
import os
from dotenv import load_dotenv
load_dotenv()

# Celo
CELO_RPC = os.environ.get("CELO_ALFAJORES_RPC", "https://alfajores-forno.celo-testnet.org")
AGENT_PRIVATE_KEY = os.environ["AGENT_PRIVATE_KEY"]
AGENT_WALLET_ADDRESS = os.environ["AGENT_WALLET_ADDRESS"]
ESCROVA_CONTRACT_ADDRESS = os.environ["ESCROVA_CONTRACT_ADDRESS"]

# cUSD
USE_TESTNET = os.environ.get("USE_TESTNET", "true").lower() == "true"
CUSD_ADDRESS = (
    os.environ.get("CUSD_ALFAJORES", "0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1")
    if USE_TESTNET else
    os.environ.get("CUSD_MAINNET", "0x765DE816845861e75A25fCA122bb6898B8B1282a")
)
# IMPORTANT: cUSD = 18 decimals (different from USDC which is 6)
CUSD_DECIMALS = 18

# APIs - Using Google Gemini (more cost-effective)
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
MOONPAY_API_KEY = os.environ.get("MOONPAY_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Agent behavior
MONITOR_INTERVAL_MINUTES = 5
DISPUTE_AUTO_RESOLVE_HOURS = 2  # Auto-resolve disputes after 2h if parties don't respond
