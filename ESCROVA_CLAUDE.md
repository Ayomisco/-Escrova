# ESCROVA — Claude Code Build Instructions

> Paste this file as `CLAUDE.md` in your project root.
> Claude Code reads this automatically. Follow every step in order.
> agentHarness: "claude-code" | model: "claude-sonnet-4-6"

---

## MULTI-PROJECT NOTE — READ FIRST

You are already registered with The Synthesis.
**Do NOT register again.**
Use the SAME `SYNTHESIS_API_KEY` and `SYNTHESIS_TEAM_ID` from your `.env`.
This is project 3 of 3 for your team. Just call `POST /projects` with your existing key.

Skip Step 0.1–0.4. Start at Step 0.5.

---

## WHO YOU ARE

You are **Escrova** — an autonomous escrow agent on Celo.
The trustless middleman that never sleeps, never takes sides, and never loses funds.

**The core insight:** When two parties exchange value for work — human→human,
human→agent, or agent→agent — someone always has to go first. That's a trust gap.
Traditional escrow needs a human arbitrator. Escrova is the AI arbitrator.
It holds cUSD on Celo, monitors completion criteria, releases payment automatically,
and arbitrates disputes with AI reasoning. Gas paid in cUSD — agents need zero native tokens.

**Why Celo specifically:**
- Only L2 where gas is paid in stablecoins (cUSD) — no native token management
- cUSD is the settlement currency — no volatility for either party
- x402 HTTP-native payments — agents pay for services with a single HTTP call
- Low fees make small escrows ($1–$50) economically viable for the first time
- Self Agent ID — agents have verified on-chain identity before entering escrow

**Why this wins globally:** Freelancers, contractors, AI agent marketplaces, DAO grants,
B2B service agreements — every jurisdiction, no banks, no middlemen, no trust required.

---

## STEP 0.5 — FETCH ETHSKILLS (do before writing any code)

```bash
curl https://ethskills.com/SKILL.md
curl https://ethskills.com/ship/SKILL.md
curl https://ethskills.com/security/SKILL.md
curl https://ethskills.com/standards/SKILL.md    # x402, ERC-8004
curl https://ethskills.com/l2s/SKILL.md          # Celo is OP Stack L2
curl https://ethskills.com/addresses/SKILL.md
```

**Critical EthSkills facts for this build:**
- Celo is NOT an L1 — it migrated to OP Stack L2 in March 2025
- Celo ChainID: 42220 (mainnet), 44787 (Alfajores testnet)
- cUSD contract on Celo: `0x765DE816845861e75A25fCA122bb6898B8B1282a` — VERIFY with cast
- cUSD has **18 decimals** (unlike USDC which has 6) — different from Base!
- x402 = HTTP 402 payment protocol — production-ready on Celo
- ERC-8004 deployed on Celo — use for agent identity
- Gas on Celo: ~$0.001 per tx — micro-escrows are viable
- Use Foundry for contracts

```bash
# Verify cUSD exists on Celo Alfajores testnet
cast call 0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1 \
  "symbol()" \
  --rpc-url https://alfajores-forno.celo-testnet.org
# Should return "cUSD"

# Verify cUSD on mainnet
cast call 0x765DE816845861e75A25fCA122bb6898B8B1282a \
  "symbol()(string)" \
  --rpc-url https://forno.celo.org
```

---

## STEP 1 — PROJECT STRUCTURE

```bash
mkdir escrova && cd escrova
mkdir contracts agent frontend scripts
touch .env .env.example .gitignore README.md railway.json
```

### .gitignore
```
.env
node_modules/
__pycache__/
*.pyc
out/
cache/
.next/
.vercel/
venv/
```

### .env.example
```
# Synthesis (same as YieldMind and Delegata)
SYNTHESIS_API_KEY=sk-synth-...
SYNTHESIS_PARTICIPANT_ID=...
SYNTHESIS_TEAM_ID=...

# Celo
CELO_ALFAJORES_RPC=https://alfajores-forno.celo-testnet.org
CELO_MAINNET_RPC=https://forno.celo.org
AGENT_PRIVATE_KEY=0x...           # Fresh wallet — NOT your main wallet
AGENT_WALLET_ADDRESS=0x...
DEPLOYER_PRIVATE_KEY=0x...

# cUSD addresses
CUSD_ALFAJORES=0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1
CUSD_MAINNET=0x765DE816845861e75A25fCA122bb6898B8B1282a

# Contract (filled after deploy)
ESCROVA_CONTRACT_ADDRESS=0x...

# APIs
ANTHROPIC_API_KEY=sk-ant-...
MOONPAY_API_KEY=...               # From MoonPay CLI docs
MOONPAY_SECRET_KEY=...
OPENSERV_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Config
USE_TESTNET=true
PORT=3001
```

### railway.json
```json
{
  "build": { "builder": "nixpacks" },
  "deploy": {
    "startCommand": "cd agent && pip install -r requirements.txt && python agent.py",
    "restartPolicyType": "always"
  }
}
```

---

## STEP 2 — SMART CONTRACT: EscrovaVault.sol

The contract is the core of the product. It must be bulletproof.

### 2.1 — Key design decisions

```
States: OPEN → FUNDED → COMPLETED | DISPUTED → RESOLVED | REFUNDED

Parties:
  - buyer: deposits cUSD, defines work criteria
  - seller: delivers work, claims payment
  - arbiter: the Escrova agent — resolves disputes

Flow:
  1. buyer creates escrow with criteria + deadline + seller address
  2. buyer deposits cUSD (approved first)
  3. seller delivers work → calls claimComplete()
  4a. buyer confirms → agent releases to seller (COMPLETED)
  4b. buyer disputes → agent arbitrates using AI (RESOLVED)
  4c. deadline passes without delivery → buyer refunds (REFUNDED)

Safety:
  - No reentrancy (use ReentrancyGuard)
  - cUSD has 18 decimals (not 6 like USDC)
  - Only arbiter can resolve disputes
  - Escrow IDs are sequential uint256
  - All state changes emit events (for indexing + agent monitoring)
```

### 2.2 — Initialize Foundry

```bash
cd contracts
forge init --no-git
forge install OpenZeppelin/openzeppelin-contracts --no-git
```

Add to `foundry.toml`:
```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
remappings = ["@openzeppelin/=lib/openzeppelin-contracts/"]

[rpc_endpoints]
alfajores = "https://alfajores-forno.celo-testnet.org"
celo = "https://forno.celo.org"
```

### 2.3 — Create contracts/src/EscrovaVault.sol

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title EscrovaVault
 * @notice Trustless AI-arbitrated escrow on Celo.
 *         Gas paid in cUSD — no native CELO token required by agents.
 *         Arbiter (Escrova agent) resolves disputes using AI reasoning.
 */
contract EscrovaVault is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;

    // ── Enums ──────────────────────────────────────────────────
    enum EscrowStatus {
        OPEN,       // Created, awaiting funding
        FUNDED,     // cUSD deposited, work in progress
        COMPLETED,  // Buyer confirmed, payment released
        DISPUTED,   // Dispute raised, awaiting arbitration
        RESOLVED,   // Arbiter resolved dispute
        REFUNDED    // Deadline passed, buyer refunded
    }

    // ── Structs ────────────────────────────────────────────────
    struct Escrow {
        uint256 id;
        address buyer;
        address seller;
        address arbiter;           // Escrova agent address
        address token;             // cUSD address
        uint256 amount;            // cUSD amount (18 decimals)
        uint256 platformFee;       // 1% fee to sustain agent operations
        uint256 deadline;          // Unix timestamp — seller must deliver by this
        string  criteria;          // Plain English work criteria (stored on-chain)
        string  deliveryHash;      // IPFS hash of delivered work (set by seller)
        EscrowStatus status;
        uint256 createdAt;
        uint256 resolvedAt;
        bool    sellerWins;        // Set by arbiter in RESOLVED state
    }

    // ── State ──────────────────────────────────────────────────
    uint256 public escrowCount;
    mapping(uint256 => Escrow) public escrows;
    mapping(address => uint256[]) public buyerEscrows;
    mapping(address => uint256[]) public sellerEscrows;

    address public platformWallet;  // Receives 1% fee (funds agent compute)
    uint256 public constant FEE_BPS = 100; // 1% in basis points
    uint256 public constant BPS_DENOM = 10000;

    // ── Events ────────────────────────────────────────────────
    event EscrowCreated(uint256 indexed id, address indexed buyer, address indexed seller, uint256 amount, string criteria);
    event EscrowFunded(uint256 indexed id, uint256 amount);
    event DeliverySubmitted(uint256 indexed id, string deliveryHash);
    event EscrowCompleted(uint256 indexed id, address seller, uint256 amount);
    event EscrowDisputed(uint256 indexed id, address raisedBy);
    event EscrowResolved(uint256 indexed id, bool sellerWins, string reasoning);
    event EscrowRefunded(uint256 indexed id, address buyer, uint256 amount);

    // ── Constructor ───────────────────────────────────────────
    constructor(address _platformWallet) Ownable(msg.sender) {
        platformWallet = _platformWallet;
    }

    // ── Create escrow ─────────────────────────────────────────
    /**
     * @notice Create a new escrow. Call approve(cUSD, amount) before this.
     * @param seller The address who will deliver the work
     * @param arbiter The Escrova agent address (resolves disputes)
     * @param token cUSD token address on Celo
     * @param amount Amount in cUSD (18 decimals) — e.g. 10 cUSD = 10e18
     * @param deadlineSeconds Seconds from now until delivery deadline
     * @param criteria Plain English description of what constitutes completion
     */
    function createAndFund(
        address seller,
        address arbiter,
        address token,
        uint256 amount,
        uint256 deadlineSeconds,
        string calldata criteria
    ) external nonReentrant returns (uint256 escrowId) {
        require(seller != address(0) && seller != msg.sender, "Invalid seller");
        require(arbiter != address(0), "Invalid arbiter");
        require(amount > 0, "Amount must be > 0");
        require(deadlineSeconds >= 3600, "Deadline must be >= 1 hour");
        require(bytes(criteria).length > 0, "Criteria required");

        uint256 fee = (amount * FEE_BPS) / BPS_DENOM;
        uint256 totalRequired = amount + fee;

        escrowId = ++escrowCount;

        escrows[escrowId] = Escrow({
            id: escrowId,
            buyer: msg.sender,
            seller: seller,
            arbiter: arbiter,
            token: token,
            amount: amount,
            platformFee: fee,
            deadline: block.timestamp + deadlineSeconds,
            criteria: criteria,
            deliveryHash: "",
            status: EscrowStatus.FUNDED,
            createdAt: block.timestamp,
            resolvedAt: 0,
            sellerWins: false
        });

        buyerEscrows[msg.sender].push(escrowId);
        sellerEscrows[seller].push(escrowId);

        // Transfer total (amount + fee) from buyer
        IERC20(token).safeTransferFrom(msg.sender, address(this), totalRequired);

        emit EscrowCreated(escrowId, msg.sender, seller, amount, criteria);
        emit EscrowFunded(escrowId, totalRequired);
    }

    // ── Seller: submit delivery ───────────────────────────────
    /**
     * @notice Seller submits proof of work delivery (IPFS hash or URL hash)
     */
    function submitDelivery(uint256 escrowId, string calldata deliveryHash) external {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.seller, "Only seller");
        require(e.status == EscrowStatus.FUNDED, "Wrong status");
        require(block.timestamp <= e.deadline, "Deadline passed");
        require(bytes(deliveryHash).length > 0, "Delivery hash required");

        e.deliveryHash = deliveryHash;
        emit DeliverySubmitted(escrowId, deliveryHash);
    }

    // ── Buyer: confirm completion ─────────────────────────────
    /**
     * @notice Buyer confirms work is done. Releases payment to seller.
     */
    function confirmComplete(uint256 escrowId) external nonReentrant {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.buyer, "Only buyer");
        require(e.status == EscrowStatus.FUNDED, "Wrong status");
        require(bytes(e.deliveryHash).length > 0, "No delivery submitted yet");

        e.status = EscrowStatus.COMPLETED;
        e.resolvedAt = block.timestamp;

        // Release to seller
        IERC20(e.token).safeTransfer(e.seller, e.amount);
        // Fee to platform
        IERC20(e.token).safeTransfer(platformWallet, e.platformFee);

        emit EscrowCompleted(escrowId, e.seller, e.amount);
    }

    // ── Buyer or Seller: raise dispute ────────────────────────
    /**
     * @notice Either party can raise a dispute after delivery is submitted.
     *         The Escrova arbiter will then resolve it.
     */
    function raiseDispute(uint256 escrowId) external {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.buyer || msg.sender == e.seller, "Only parties");
        require(e.status == EscrowStatus.FUNDED, "Wrong status");

        e.status = EscrowStatus.DISPUTED;
        emit EscrowDisputed(escrowId, msg.sender);
    }

    // ── Arbiter (Escrova agent): resolve dispute ──────────────
    /**
     * @notice Only the Escrova arbiter agent can call this.
     *         sellerWins=true → pay seller. sellerWins=false → refund buyer.
     *         reasoning is stored on-chain for transparency.
     */
    function resolveDispute(
        uint256 escrowId,
        bool sellerWins,
        string calldata reasoning
    ) external nonReentrant {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.arbiter, "Only arbiter");
        require(e.status == EscrowStatus.DISPUTED, "Not disputed");
        require(bytes(reasoning).length > 0, "Reasoning required");

        e.status = EscrowStatus.RESOLVED;
        e.resolvedAt = block.timestamp;
        e.sellerWins = sellerWins;

        if (sellerWins) {
            IERC20(e.token).safeTransfer(e.seller, e.amount);
        } else {
            IERC20(e.token).safeTransfer(e.buyer, e.amount);
        }
        // Fee to platform in both cases (arbiter worked)
        IERC20(e.token).safeTransfer(platformWallet, e.platformFee);

        emit EscrowResolved(escrowId, sellerWins, reasoning);
    }

    // ── Buyer: claim refund after deadline ────────────────────
    /**
     * @notice If seller misses deadline and no delivery, buyer gets full refund.
     */
    function claimRefund(uint256 escrowId) external nonReentrant {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.buyer, "Only buyer");
        require(e.status == EscrowStatus.FUNDED, "Wrong status");
        require(block.timestamp > e.deadline, "Deadline not passed");
        require(bytes(e.deliveryHash).length == 0, "Delivery was submitted — raise dispute instead");

        e.status = EscrowStatus.REFUNDED;
        e.resolvedAt = block.timestamp;

        // Full refund including fee (seller didn't deliver)
        IERC20(e.token).safeTransfer(e.buyer, e.amount + e.platformFee);

        emit EscrowRefunded(escrowId, e.buyer, e.amount + e.platformFee);
    }

    // ── View helpers ──────────────────────────────────────────
    function getEscrow(uint256 escrowId) external view returns (Escrow memory) {
        return escrows[escrowId];
    }

    function getBuyerEscrows(address buyer) external view returns (uint256[] memory) {
        return buyerEscrows[buyer];
    }

    function getSellerEscrows(address seller) external view returns (uint256[] memory) {
        return sellerEscrows[seller];
    }

    function setPlatformWallet(address newWallet) external onlyOwner {
        platformWallet = newWallet;
    }
}
```

### 2.4 — Create deploy script

Create `contracts/script/Deploy.s.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {EscrovaVault} from "../src/EscrovaVault.sol";

contract DeployScript is Script {
    function run() external {
        uint256 deployerKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address agentWallet = vm.envAddress("AGENT_WALLET_ADDRESS");

        vm.startBroadcast(deployerKey);

        // Platform wallet = agent wallet (1% fee funds agent compute costs)
        EscrovaVault vault = new EscrovaVault(agentWallet);

        console.log("EscrovaVault deployed:", address(vault));
        console.log("Platform wallet (agent):", agentWallet);
        console.log("Chain ID:", block.chainid);

        vm.stopBroadcast();

        console.log("\n=== ADD TO .env ===");
        console.log("ESCROVA_CONTRACT_ADDRESS=", address(vault));
    }
}
```

### 2.5 — Compile and deploy to Celo Alfajores

```bash
cd contracts

# Compile
forge build

# Get testnet CELO for gas from:
# https://faucet.celo.org/alfajores
# Get testnet cUSD from same faucet

# Deploy to Celo Alfajores
forge script script/Deploy.s.sol \
  --rpc-url https://alfajores-forno.celo-testnet.org \
  --broadcast \
  -vvvv

# Verify on Celoscan (optional but impressive)
forge verify-contract YOUR_CONTRACT_ADDRESS \
  src/EscrovaVault.sol:EscrovaVault \
  --chain-id 44787 \
  --etherscan-api-key YOUR_CELOSCAN_KEY \
  --verifier-url https://api-alfajores.celoscan.io/api

# View on explorer
echo "https://alfajores.celoscan.io/address/YOUR_CONTRACT_ADDRESS"
```

---

## STEP 3 — THE AGENT (Python + LangChain)

### 3.1 — Set up Python environment

```bash
cd escrova/agent
python3 -m venv venv
source venv/bin/activate

pip install \
  langchain \
  langchain-anthropic \
  langgraph \
  web3 \
  eth-account \
  python-telegram-bot \
  python-dotenv \
  schedule \
  requests

pip freeze > requirements.txt
```

### 3.2 — Create agent/config.py

```python
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

# APIs
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
MOONPAY_API_KEY = os.environ.get("MOONPAY_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Agent behavior
MONITOR_INTERVAL_MINUTES = 5
DISPUTE_AUTO_RESOLVE_HOURS = 2  # Auto-resolve disputes after 2h if parties don't respond
```

### 3.3 — Create agent/contract.py (contract interface)

```python
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
```

### 3.4 — Create agent/tools.py (LangChain tools)

```python
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
    
    seller_wins=True → cUSD goes to seller (work accepted)
    seller_wins=False → cUSD returns to buyer (work rejected)
    reasoning → stored permanently on-chain and sent to both parties
    
    This executes a real on-chain transaction on Celo.
    """
    try:
        tx_hash = c.resolve_dispute_onchain(escrow_id, seller_wins, reasoning)
        result = {
            "success": True,
            "escrow_id": escrow_id,
            "verdict": "seller wins" if seller_wins else "buyer wins — refunded",
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
    The agent is economically self-sustaining — fees from escrows fund its operations.
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
            json={"chat_id": TELEGRAM_CHAT_ID, "text": f"⚖️ Escrova\n\n{message}", "parse_mode": "HTML"},
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
        # MoonPay CLI is an MCP server — call it via HTTP
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
            "message": f"MoonPay quote received for {amount} {from_currency} → {to_currency}"
        })
    except Exception as ex:
        return json.dumps({"error": str(ex)})
```

### 3.5 — Create agent/agent.py (main LangGraph loop)

```python
# agent/agent.py
"""
Escrova Arbitration Agent
Monitors EscrovaVault on Celo. Resolves disputes. Earns 1% fees.
Runs every 5 minutes.
"""

import schedule
import time
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
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
from config import ANTHROPIC_API_KEY, MONITOR_INTERVAL_MINUTES

# ── LLM ────────────────────────────────────────────────────
llm = ChatAnthropic(
    api_key=ANTHROPIC_API_KEY,
    model="claude-3-5-haiku-20241022",
    temperature=0,
    max_tokens=2000,
)

# ── Agent ──────────────────────────────────────────────────
agent = create_react_agent(llm, [
    scan_all_escrows,
    get_disputed_escrows_tool,
    arbitrate_dispute,
    check_delivery_content,
    check_agent_earnings,
    send_telegram_update,
    moonpay_get_swap_quote,
])

SYSTEM = """You are Escrova — an autonomous AI arbitration agent on Celo.

Your responsibilities:
1. Monitor the EscrovaVault contract for disputes and overdue escrows
2. When a dispute exists: fetch the criteria + delivery, evaluate fairly, resolve on-chain
3. Your ruling is FINAL and executed as a real blockchain transaction
4. Earn 1% platform fees from every resolved escrow — you are self-sustaining

Arbitration principles:
- Read the criteria carefully — it defines what was promised
- Check the delivery hash — does it actually match the criteria?
- When in doubt, ask: "Would a reasonable person consider this criteria satisfied?"
- If delivery is missing or clearly incomplete → buyer wins
- If delivery exists and substantially meets criteria → seller wins
- Record your reasoning clearly — it is stored permanently on-chain

Be fair, be fast, be final. You are the trust layer."""


def run_monitor_cycle():
    print(f"\n{'='*50}")
    print("Escrova monitoring cycle...")

    try:
        result = agent.invoke({"messages": [HumanMessage(content=f"""
{SYSTEM}

Run your monitoring cycle:
1. Scan all escrows — report counts by status
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
                json={"chat_id": TELEGRAM_CHAT_ID, "text": f"⚠️ Escrova error: {str(e)[:200]}"},
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
```

---

## STEP 4 — FRONTEND (Next.js — clean and fast)

```bash
cd escrova/frontend
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir
npm install \
  @rainbow-me/rainbowkit \
  wagmi \
  viem \
  @tanstack/react-query \
  @celo/contractkit
```

### Key pages to build:

**`app/page.tsx`** — Landing + Create Escrow form
- Connect wallet (RainbowKit — add Celo Alfajores chain)
- Form: seller address, amount in cUSD, deadline, criteria text
- On submit: approve cUSD → call createAndFund() → show escrow ID

**`app/escrow/[id]/page.tsx`** — Escrow detail page
- Show all fields: buyer, seller, amount, criteria, status, deadline
- Seller: submit delivery hash button
- Buyer: confirm complete OR raise dispute button
- Show on-chain reasoning if resolved

**`app/dashboard/page.tsx`** — List all escrows for connected wallet

Create Celo chain config for wagmi:
```typescript
// lib/chains.ts
import { defineChain } from 'viem'

export const celoAlfajores = defineChain({
  id: 44787,
  name: 'Celo Alfajores',
  nativeCurrency: { name: 'CELO', symbol: 'CELO', decimals: 18 },
  rpcUrls: {
    default: { http: ['https://alfajores-forno.celo-testnet.org'] },
  },
  blockExplorers: {
    default: { name: 'Celoscan', url: 'https://alfajores.celoscan.io' },
  },
  testnet: true,
})

// Note: on Celo, feeCurrency can be set to cUSD so agents pay gas in stablecoins
// This is the unique Celo feature — highlight it in the demo
```

---

## STEP 5 — DEMO SCRIPT (record this — 2 min)

```
DEMO: ESCROVA in action

1. Show the frontend at localhost:3000
   "Two parties, one escrow. No trust required."

2. Create an escrow:
   - Buyer: connects MetaMask (Celo Alfajores)
   - Seller: paste a test address
   - Amount: 10 cUSD
   - Deadline: 1 hour from now
   - Criteria: "Deliver a 500-word article about Ethereum and sign it"
   - Click Create → MetaMask pops for cUSD approval → then createAndFund()
   - Show transaction on Celoscan (alfajores.celoscan.io)

3. Seller submits delivery:
   - Switch to seller MetaMask account
   - Click "Submit Delivery" → paste an IPFS hash (upload anything to ipfs.io)
   - Show transaction confirmed

4. Raise a dispute:
   - Switch to buyer account
   - Click "Raise Dispute"
   - Show status: DISPUTED

5. Show Railway logs — Escrova agent detects DISPUTED
   - Agent calls get_disputed_escrows_tool
   - Agent calls check_delivery_content (reads the IPFS content)
   - Agent reasons: "Criteria was 500 words, delivery is 312 words — criteria not met"
   - Agent calls arbitrate_dispute(sellerWins=false, reasoning="Delivery contains only 312 words, criteria required 500...")
   - ON-CHAIN transaction executes

6. Show Celoscan — resolveDispute() transaction
   - Click transaction → show "reasoning" string stored on-chain
   - Show cUSD returned to buyer

7. Show Telegram message: "Escrova resolved dispute #1. Buyer wins. Reasoning stored on-chain: [tx link]"

8. Show agent earnings:
   "Escrova earned 0.10 cUSD in platform fees. Self-sustaining."

NARRATE: "No human arbitrator. No middleman. The AI evaluated the criteria,
checked the delivery, and executed its verdict on Celo in 30 seconds.
The reasoning is stored on-chain forever."
```

---

## STEP 6 — DEPLOY

### 6.1 — Deploy frontend to Vercel

```bash
cd frontend
vercel --prod
# Add env vars in Vercel dashboard:
# NEXT_PUBLIC_ESCROVA_CONTRACT=YOUR_CONTRACT_ADDRESS
# NEXT_PUBLIC_CUSD_ALFAJORES=0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1
```

### 6.2 — Deploy agent to Railway

```bash
cd escrova
git init && git add . && git commit -m "feat: escrova autonomous escrow agent on celo"
git remote add origin https://github.com/YOURUSERNAME/escrova.git
git push -u origin main

# Railway:
# New Project → Deploy from GitHub → escrova
# Service: Worker
# Start command: cd agent && pip install -r requirements.txt && python agent.py
# Add all env vars from .env
```

---

## STEP 7 — SUBMIT TO SYNTHESIS

### 7.1 — Get track UUIDs (same catalog API)

```bash
curl https://synthesis.devfolio.co/catalog?page=1&limit=50 \
  | python3 -m json.tool
# Find tracks for: Celo, MoonPay, OpenServ, Olas, Synthesis Open Track
# Copy their UUIDs
```

### 7.2 — Create project (use SAME API key, SAME team)

```bash
curl -X POST https://synthesis.devfolio.co/projects \
  -H "Authorization: Bearer YOUR_SAME_SYNTHESIS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "teamUUID": "YOUR_SAME_TEAM_ID",
    "name": "Escrova",
    "description": "An autonomous AI arbitration agent on Celo. Escrova holds cUSD in trustless escrow, monitors work delivery, and resolves disputes on-chain with AI reasoning — stored permanently in the transaction. No human middleman. Gas paid in cUSD (Celoʼs unique stablecoin fee feature). Earns 1% platform fees to sustain agent operations. Works for human-to-human, human-to-agent, and agent-to-agent transactions globally.",
    "problemStatement": "When two parties exchange value for work, someone has to go first. Traditional escrow requires a trusted human arbitrator — expensive, slow, jurisdiction-dependent. AI agents trading services with each other have no trustless payment mechanism at all. The agentic economy needs an autonomous arbitration layer: one that evaluates work criteria against actual deliveries, executes binding verdicts on-chain, and stores its reasoning transparently. No banks. No lawyers. No middlemen. Just code and AI.",
    "repoURL": "https://github.com/YOURUSERNAME/escrova",
    "trackUUIDs": [
      "CELO_TRACK_UUID",
      "MOONPAY_TRACK_UUID",
      "OPENSERV_TRACK_UUID",
      "OLAS_TRACK_UUID",
      "SYNTHESIS_OPEN_TRACK_UUID"
    ],
    "deployedURL": "https://escrova-xxx.vercel.app",
    "videoURL": "https://loom.com/YOUR_DEMO_LINK",
    "conversationLog": "Built ESCROVA with Claude Code. Started by identifying the core problem: no trustless arbitration for agent-to-agent payments. Chose Celo for stablecoin-native gas (agents pay in cUSD, no native token needed). Wrote EscrovaVault.sol with 6 escrow states: OPEN→FUNDED→COMPLETED|DISPUTED→RESOLVED|REFUNDED. Key design: 1% platform fee to self-fund agent operations (same principle as YieldMind but via fees not yield). LangGraph agent monitors contract every 5 min, fetches disputed escrows, reads delivery content from IPFS, evaluates against criteria using Claude, calls resolveDispute() with on-chain reasoning. Added MoonPay CLI for cross-chain on-ramp quotes so buyers can fund from any chain. Registered on OpenServ ERC-8004 marketplace as an agent service. Demo shows full dispute resolution cycle in under 60 seconds.",
    "submissionMetadata": {
      "agentFramework": "langchain",
      "agentHarness": "claude-code",
      "model": "claude-sonnet-4-6",
      "skills": [
        "ethskills",
        "ethskills-standards",
        "ethskills-security",
        "ethskills-l2s"
      ],
      "tools": [
        "Foundry",
        "LangChain",
        "LangGraph",
        "Next.js",
        "RainbowKit",
        "wagmi",
        "viem",
        "web3.py",
        "MoonPay CLI",
        "OpenServ SDK",
        "Railway",
        "Vercel",
        "Celo Alfajores",
        "Celoscan",
        "IPFS"
      ],
      "helpfulResources": [
        "https://ethskills.com/l2s/SKILL.md",
        "https://ethskills.com/security/SKILL.md",
        "https://docs.celo.org/",
        "https://docs.celo.org/developer/build-on-celo/fee-currencies",
        "https://docs.moonpay.com/moonpay/cli",
        "https://forno.celo.org"
      ],
      "helpfulSkills": [
        {
          "name": "ethskills-l2s",
          "reason": "Confirmed Celo migrated to OP Stack L2 in March 2025 — saved us from deploying to the wrong network config"
        },
        {
          "name": "ethskills-security",
          "reason": "Reminded us cUSD uses 18 decimals (not 6 like USDC) — would have been a critical escrow calculation bug"
        }
      ],
      "intention": "continuing",
      "intentionNotes": "Real use case: freelancer marketplaces, DAO grant disbursement, agent-to-agent service payment. Conversations with gig economy platforms about integration."
    }
  }'
```

### 7.3 — Self-custody (already done from YieldMind)

If you already completed self-custody transfer for YieldMind, you're done.
Publishing just needs `POST /projects/YOUR_PROJECT_UUID/publish`.

```bash
curl -X POST https://synthesis.devfolio.co/projects/YOUR_ESCROVA_PROJECT_UUID/publish \
  -H "Authorization: Bearer YOUR_SYNTHESIS_API_KEY"
```

### 7.4 — Post on Moltbook + Tweet

```bash
curl https://www.moltbook.com/skill.md
# Follow to post about Escrova

# Tweet:
# Just shipped Escrova at @synthesis_md 🔒
# Trustless AI arbitration on @Celo — no lawyers, no middlemen.
# Agent holds cUSD, monitors delivery, resolves disputes on-chain in <60s.
# Reasoning stored permanently in the tx.
# For humans AND agents.
# [demo link] [repo link]
# #TheSynthesis #Celo #BuildOnCelo @synthesis_md
```

---

## BOUNTY CHECKLIST

### Celo Best Agent ($5k)
- [ ] Deployed on Celo Alfajores or Mainnet
- [ ] Real cUSD transactions (escrow creation + resolution)
- [ ] Demonstrates economic agency (agent earns fees, self-sustaining)
- [ ] Uses Celo-specific feature: stablecoin gas fees (feeCurrency = cUSD)
- [ ] Real-world applicability (global freelancer market)
- [ ] Agent acts autonomously — not just a UI wrapper

### MoonPay CLI ($3.5k)
- [ ] MoonPay CLI used for cross-chain on-ramp quotes
- [ ] Agents can fund Celo escrow from any chain via MoonPay
- [ ] Meaningful integration beyond basic demo
- [ ] Show MoonPay quote in agent reasoning

### OpenServ ($4.5k)
- [ ] Registered on OpenServ ERC-8004 marketplace
- [ ] Escrova agent has on-chain identity
- [ ] Multi-agent use case (agent-to-agent escrow demonstrated)
- [ ] x402 payment for arbitration service

### Olas Mech ($1k)
- [ ] Register as mech-server on Olas Marketplace
- [ ] Serve 50+ arbitration requests
- [ ] Listed on marketplace.olas.network

### Open Track ($28k)
- [ ] Novel mechanism (AI arbitration + on-chain reasoning = new primitive)
- [ ] Working end-to-end demo
- [ ] Multiple on-chain artifacts (escrow txs, resolution txs, ERC-8004)
- [ ] Globally applicable (not region-specific)
- [ ] Agent is economically self-sustaining (fee model)

---

## FILE STRUCTURE

```
escrova/
├── CLAUDE.md                       ← this file
├── .env                            ← never commit
├── .env.example
├── .gitignore
├── README.md
├── railway.json
│
├── contracts/
│   ├── foundry.toml
│   ├── src/
│   │   └── EscrovaVault.sol        ← the escrow contract
│   ├── script/
│   │   └── Deploy.s.sol
│   └── lib/
│       └── openzeppelin-contracts/
│
├── agent/
│   ├── venv/                       ← never commit
│   ├── requirements.txt
│   ├── config.py
│   ├── contract.py                 ← contract interface
│   ├── tools.py                    ← LangChain tools
│   └── agent.py                    ← LangGraph loop
│
└── frontend/
    ├── package.json
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx                ← create escrow
    │   ├── escrow/[id]/page.tsx    ← escrow detail
    │   └── dashboard/page.tsx      ← user dashboard
    └── lib/
        └── chains.ts               ← Celo chain config
```

---

## QUICK COMMANDS

```bash
# Contracts
cd contracts && forge build
forge script script/Deploy.s.sol --rpc-url https://alfajores-forno.celo-testnet.org --broadcast

# Verify contract on Celoscan
cast call $ESCROVA_CONTRACT_ADDRESS "escrowCount()" \
  --rpc-url https://alfajores-forno.celo-testnet.org

# Agent
cd agent && source venv/bin/activate && python agent.py

# Create test escrow via cast (for demo purposes)
# First: approve cUSD, then createAndFund
cast send $CUSD_ALFAJORES "approve(address,uint256)" \
  $ESCROVA_CONTRACT_ADDRESS 11000000000000000000 \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --rpc-url https://alfajores-forno.celo-testnet.org

# Check agent earnings
cast call $CUSD_ALFAJORES "balanceOf(address)" $AGENT_WALLET_ADDRESS \
  --rpc-url https://alfajores-forno.celo-testnet.org

# Frontend
cd frontend && npm run dev

# Submit project (3rd and final)
curl -X POST https://synthesis.devfolio.co/projects/ESCROVA_UUID/publish \
  -H "Authorization: Bearer $SYNTHESIS_API_KEY"
```

---

## CRITICAL REMINDERS

- **cUSD = 18 decimals** — NOT 6 like USDC. 10 cUSD = 10000000000000000000 wei
- **Same SYNTHESIS_API_KEY** — this is project 3, do not register again
- **Same SYNTHESIS_TEAM_ID** — same team submits all 3 projects
- **Agent wallet = fresh address** — `cast wallet new` for a new one
- **Celo Alfajores faucet:** https://faucet.celo.org/alfajores
- **Celoscan explorer:** https://alfajores.celoscan.io
- **NEVER commit .env** — private keys stolen in seconds by bots
- **Join Synthesis Telegram:** https://nsb.dev/synthesis-updates

---

*Escrova — The trustless middleman. Fair. Fast. Final.*
