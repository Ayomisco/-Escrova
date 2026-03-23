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

vault = w3.eth.contract(
    address=Web3.to_checksum_address(ESCROVA_CONTRACT_ADDRESS),
    abi=VAULT_ABI
)
cusd = w3.eth.contract(
    address=Web3.to_checksum_address(CUSD_ADDRESS),
    abi=CUSD_ABI
)

STATUS_NAMES = {0: "OPEN", 1: "FUNDED", 2: "COMPLETED", 3: "DISPUTED", 4: "RESOLVED", 5: "REFUNDED"}


def get_all_escrows() -> list[dict]:
    """Read all escrows from the contract."""
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
                "delivery_hash": e[9],
                "status": STATUS_NAMES.get(e[10], "UNKNOWN"),
                "status_int": e[10],
                "created_at": e[11],
            })
        except Exception as ex:
            print(f"Error reading escrow {i}: {ex}")
    return escrows


def get_disputed_escrows() -> list[dict]:
    """Return only DISPUTED escrows — the agent needs to act on these."""
    return [e for e in get_all_escrows() if e["status"] == "DISPUTED"]


def get_overdue_escrows() -> list[dict]:
    """Return FUNDED escrows past their deadline with no delivery."""
    import time
    now = int(time.time())
    return [
        e for e in get_all_escrows()
        if e["status"] == "FUNDED"
        and e["deadline"] < now
        and not e["delivery_hash"]
    ]


def resolve_dispute_onchain(escrow_id: int, seller_wins: bool, reasoning: str) -> str:
    """
    Call resolveDispute on EscrovaVault. Only callable by the arbiter (this agent).
    Returns transaction hash.
    """
    nonce = w3.eth.get_transaction_count(agent.address)
    tx = vault.functions.resolveDispute(
        escrow_id, seller_wins, reasoning
    ).build_transaction({
        "from": agent.address,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.eth.gas_price,
        "chainId": w3.eth.chain_id,
    })
    signed = agent.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise Exception(f"Transaction failed: {tx_hash.hex()}")
    return tx_hash.hex()


def agent_cusd_balance() -> float:
    """Check agent's cUSD balance (1% fees accumulate here)."""
    balance_wei = cusd.functions.balanceOf(agent.address).call()
    return float(w3.from_wei(balance_wei, "ether"))
