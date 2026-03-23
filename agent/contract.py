# agent/contract.py
"""Interface to EscrovaVault on Celo."""

from web3 import Web3
from eth_account import Account
from config import (
    CELO_RPC, AGENT_PRIVATE_KEY, AGENT_WALLET_ADDRESS,
    ESCROVA_CONTRACT_ADDRESS, CUSD_ADDRESS, CUSD_DECIMALS
)

w3 = Web3(Web3.HTTPProvider(CELO_RPC))
agent = Account.from_key(AGENT_PRIVATE_KEY)

# Minimal ABI — only what the agent needs
VAULT_ABI = [
    {"name": "escrowCount", "type": "function", "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "getEscrow", "type": "function", "inputs": [{"name": "escrowId", "type": "uint256"}], "outputs": [{"type": "tuple", "components": [
        {"name": "id", "type": "uint256"},
        {"name": "buyer", "type": "address"},
        {"name": "seller", "type": "address"},
        {"name": "arbiter", "type": "address"},
        {"name": "token", "type": "address"},
        {"name": "amount", "type": "uint256"},
        {"name": "platformFee", "type": "uint256"},
        {"name": "deadline", "type": "uint256"},
        {"name": "criteria", "type": "string"},
        {"name": "deliveryHash", "type": "string"},
        {"name": "status", "type": "uint8"},
        {"name": "createdAt", "type": "uint256"},
        {"name": "resolvedAt", "type": "uint256"},
        {"name": "sellerWins", "type": "bool"},
    ]}], "stateMutability": "view"},
    {"name": "resolveDispute", "type": "function", "inputs": [
        {"name": "escrowId", "type": "uint256"},
        {"name": "sellerWins", "type": "bool"},
        {"name": "reasoning", "type": "string"},
    ], "outputs": [], "stateMutability": "nonpayable"},
]

CUSD_ABI = [
    {"name": "balanceOf", "type": "function", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "approve", "type": "function", "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"type": "bool"}], "stateMutability": "nonpayable"},
]

# Initialize contracts — skip if placeholder address
vault = None
cusd = None

try:
    if ESCROVA_CONTRACT_ADDRESS and not ESCROVA_CONTRACT_ADDRESS.startswith("0x["):
        vault = w3.eth.contract(
            address=Web3.to_checksum_address(ESCROVA_CONTRACT_ADDRESS),
            abi=VAULT_ABI
        )
    if CUSD_ADDRESS and not CUSD_ADDRESS.startswith("0x["):
        cusd = w3.eth.contract(
            address=Web3.to_checksum_address(CUSD_ADDRESS),
            abi=CUSD_ABI
        )
except ValueError as e:
    print(f"⚠️  Warning: Could not initialize contracts: {e}")
    print("   Update ESCROVA_CONTRACT_ADDRESS in .env with real address")

STATUS_NAMES = {0: "OPEN", 1: "FUNDED", 2: "COMPLETED", 3: "DISPUTED", 4: "RESOLVED", 5: "REFUNDED"}


def get_all_escrows() -> list[dict]:
    """Read all escrows from the contract."""
    if not vault:
        return []
    count = vault.functions.escrowCount().call()
    escrows = []
    for i in range(1, count + 1):
        try:
            e = vault.functions.getEscrow(i).call()
            escrows.append({
                "id": e[0],
                "buyer": e[1],
                "seller": e[2],
                "arbiter": e[3],
                "amount_cusd": float(w3.from_wei(e[5], "ether")),  # cUSD = 18 decimals
                "deadline": e[7],
                "criteria": e[8],
                "deliveryHash": e[9],
                "status": STATUS_NAMES.get(e[10], "UNKNOWN"),
                "createdAt": e[11],
            })
        except Exception as err:
            print(f"Error reading escrow {i}: {err}")
    return escrows


def resolve_dispute(escrow_id: int, seller_wins: bool, reasoning: str) -> bool:
    """Resolve a dispute and store reasoning on-chain."""
    if not vault:
        print("❌ Vault not initialized. Deploy contract first.")
        return False
    
    try:
        tx = vault.functions.resolveDispute(
            escrow_id,
            seller_wins,
            reasoning
        ).build_transaction({
            "from": AGENT_WALLET_ADDRESS,
            "nonce": w3.eth.get_transaction_count(AGENT_WALLET_ADDRESS),
            "gas": 500_000,
            "gasPrice": w3.eth.gas_price,
        })
        
        signed = w3.eth.account.sign_transaction(tx, AGENT_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        print(f"✅ Dispute resolved: {tx_hash.hex()}")
        return True
    except Exception as e:
        print(f"❌ Error resolving dispute: {e}")
        return False
