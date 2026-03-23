# Escrova Deployment Guide

This guide walks you through deploying Escrova to production: smart contract on Celo, agent on Railway, frontend on Vercel.

## Prerequisites

Before starting:
- Celo Alfajores testnet CELO and cUSD (from https://faucet.celo.org/alfajores)
- MetaMask or similar wallet connected to Celo Alfajores
- GitHub account
- Railway account (https://railway.app)
- Vercel account (https://vercel.com)
- Telegram bot token and chat ID (for agent alerts)

## Step 6.1: Deploy Smart Contract to Celo Alfajores

### 1. Create a deployer wallet
```bash
# Generate a new wallet (do NOT use your main wallet)
cast wallet new

# Or import an existing private key
export DEPLOYER_PRIVATE_KEY=0x...
```

### 2. Fund the deployer wallet
- Go to https://faucet.celo.org/alfajores
- Request testnet CELO (needed for gas)
- Request testnet cUSD (for testing)

### 3. Set environment variables
```bash
# In escrova/.env
DEPLOYER_PRIVATE_KEY=0x...        # From step 1
AGENT_PRIVATE_KEY=0x...           # Another fresh wallet
AGENT_WALLET_ADDRESS=0x...        # Public address of agent wallet
USE_TESTNET=true
CELO_ALFAJORES_RPC=https://alfajores-forno.celo-testnet.org
```

### 4. Deploy the contract
```bash
cd contracts
forge script script/Deploy.s.sol \
  --rpc-url https://alfajores-forno.celo-testnet.org \
  --broadcast \
  -vvvv
```

### 5. Verify deployment
- Copy the contract address from the output
- Visit https://alfajores.celoscan.io/address/YOUR_CONTRACT_ADDRESS
- Verify contract source code (optional but recommended):
```bash
forge verify-contract YOUR_CONTRACT_ADDRESS \
  src/EscrovaVault.sol:EscrovaVault \
  --chain-id 44787 \
  --etherscan-api-key YOUR_CELOSCAN_KEY \
  --verifier-url https://api-alfajores.celoscan.io/api
```

### 6. Update .env with contract address
```bash
# In escrova/.env
ESCROVA_CONTRACT_ADDRESS=0x...
```

---

## Step 6.2: Deploy Agent to Railway

### 1. Initialize Git repository
```bash
cd escrova
git init
git add .
git commit -m "feat: escrova autonomous escrow agent on celo"
```

### 2. Create GitHub repository
```bash
# Create a new repo on GitHub: https://github.com/new
# Then:
git remote add origin https://github.com/YOUR_USERNAME/escrova.git
git branch -M main
git push -u origin main
```

### 3. Create Railway project
- Go to https://railway.app
- Click "New Project"
- Select "Deploy from GitHub"
- Authorize GitHub and select your escrova repository
- Railway will auto-detect railway.json and start deployment

### 4. Configure Railway service
In the Railway dashboard:
- Service name: escrova-agent
- Start command: `cd agent && pip install -r requirements.txt && python agent.py`

### 5. Add environment variables in Railway
Railway → Variables → Add all from your .env:
```
SYNTHESIS_API_KEY=...
SYNTHESIS_PARTICIPANT_ID=...
SYNTHESIS_TEAM_ID=...
CELO_ALFAJORES_RPC=...
AGENT_PRIVATE_KEY=...
AGENT_WALLET_ADDRESS=...
ESCROVA_CONTRACT_ADDRESS=...
CUSD_ALFAJORES=...
ANTHROPIC_API_KEY=...
MOONPAY_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
USE_TESTNET=true
```

### 6. Monitor logs
- Railway dashboard → Logs tab
- You should see: "Escrova starting..." and "Escrova monitoring cycle..."

---

## Step 6.3: Deploy Frontend to Vercel

### 1. Install Vercel CLI
```bash
npm install -g vercel
```

### 2. Deploy
```bash
cd frontend
vercel --prod
```

### 3. Configure environment variables
In Vercel dashboard → Settings → Environment Variables, add:
```
NEXT_PUBLIC_ESCROVA_CONTRACT=YOUR_CONTRACT_ADDRESS
NEXT_PUBLIC_CUSD_ALFAJORES=0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1
```

### 4. Visit your deployment
```
https://escrova-[random].vercel.app
```

---

## Testing the Full Stack

### 1. Create a test escrow
- Go to your Vercel frontend
- Connect MetaMask (Celo Alfajores)
- Create an escrow with:
  - Amount: 1 cUSD (small test amount)
  - Deadline: 1 hour
  - Criteria: "Deliver proof of work"

### 2. Check Railway logs
- Agent should detect the new escrow in its monitoring cycle
- Logs: "Found 1 FUNDED escrow"

### 3. Raise a test dispute
- Create a delivery
- Raise a dispute
- Watch agent arbitrate in the logs

### 4. Verify on Celoscan
- Go to https://alfajores.celoscan.io
- Find your contract address
- Click on escrow transactions
- Verify resolveDispute() was called with reasoning stored on-chain

---

## Troubleshooting

### Agent not starting
- Check Railway logs for Python errors
- Verify ANTHROPIC_API_KEY is set
- Verify contract address is valid on Alfajores

### Transaction failures
- Ensure agent wallet has testnet CELO for gas
- Ensure contract is deployed to the correct address
- Check that cUSD addresses match Alfajores testnet

### MetaMask connection issues
- Switch to Celo Alfajores network
- Add chain if not present: https://docs.celo.org/docs/learn/adding-celo-to-metamask

### Agent not detecting disputes
- Check that Railway service is running
- Verify env vars are set correctly
- Check contract ABI matches the compiled contract

---

## Next Steps: Deployment to Mainnet

When ready to deploy to Celo mainnet:

1. Deploy contract with `--rpc-url https://forno.celo.org`
2. Update CUSD_MAINNET address: 0x765DE816845861e75A25fCA122bb6898B8B1282a
3. Update Railway env vars to use mainnet RPC
4. Update frontend env vars to mainnet contract address
5. Set USE_TESTNET=false

---

## Key Configuration Files

- **contracts/foundry.toml** — Foundry config with Celo RPC endpoints
- **contracts/script/Deploy.s.sol** — Deployment script
- **agent/requirements.txt** — Python dependencies
- **agent/config.py** — Agent configuration from env
- **agent/agent.py** — Main agent loop (runs every 5 minutes)
- **railway.json** — Railway deployment config
- **frontend/package.json** — Node dependencies
- **frontend/lib/chains.ts** — Celo Alfajores chain config

---

## Monitoring

### Agent Earnings
Check agent's cUSD balance in Railway logs:
```
Agent has earned 0.XX cUSD from platform fees
```

### Escrow Activity
Check Celoscan for all contract calls:
https://alfajores.celoscan.io/address/YOUR_CONTRACT_ADDRESS

### Telegram Alerts
Agent sends Telegram updates when:
- Dispute is raised
- Dispute is resolved
- Error occurs

---

## Security Notes

- **Private keys**: Never commit to GitHub. Use Railway/Vercel secrets only.
- **Agent wallet**: Keep separate from your main wallet. It's a hot wallet.
- **Platform fee wallet**: Can be agent wallet or separate address.
- **cUSD approval**: Frontend must handle ERC20 approval before calling createAndFund().

---

## Support

- Celo docs: https://docs.celo.org/
- Foundry book: https://book.getfoundry.sh/
- LangChain docs: https://python.langchain.com/
- Railway docs: https://docs.railway.app/
- Vercel docs: https://vercel.com/docs
