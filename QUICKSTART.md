# Escrova — Quick Start Deployment Guide

This guide gets you from zero to deployed in ~30 minutes.

## ✅ Prerequisites Checklist

- [ ] MetaMask with Celo Alfajores configured
- [ ] Testnet CELO + cUSD from https://faucet.celo.org/alfajores
- [ ] Node.js 18+ installed
- [ ] Python 3.9+ installed
- [ ] Foundry installed (`forge --version` works)
- [ ] GitHub repo set up: https://github.com/Ayomisco/-Escrova
- [ ] Railway account: https://railway.app
- [ ] Vercel account: https://vercel.com
- [ ] Gemini API key ready: AIzaSyBsPDY16KUF4UTVS7ZcmtflT_F-rA5zypg
- [ ] Telegram bot token: 8650450273:AAHib-U-a8abonUeSOxLYf-aMKSxRaTpALk
- [ ] Telegram chat ID: 5067554737

## 🚀 Step 1: Deploy Smart Contract (5 minutes)

```bash
cd /Users/ayomisco/Documents/Main/Hackathons/SYNTHESIS\ Hack/escrova/contracts

# Deploy to Celo Alfajores testnet
forge script script/Deploy.s.sol \
  --rpc-url https://alfajores-forno.celo-testnet.org \
  --broadcast \
  --private-key 2732982db8296a98492c484054d0092c7099f63245af9c67502cf3be7c90fdfa \
  -vvvv
```

**What you'll see**:
```
EscrovaVault deployed: 0x...
Platform wallet (agent): 0xD8a6beB35E3516338dcFF641538d3984C353E503
```

**Save the contract address** → Update in `.env` as `ESCROVA_CONTRACT_ADDRESS`

**Verify on Celoscan**: https://alfajores.celoscan.io/address/YOUR_ADDRESS

## 🚀 Step 2: Deploy Agent to Railway (10 minutes)

### 2.1 Update .env file

```bash
# In escrova/.env, ensure these are set:
ESCROVA_CONTRACT_ADDRESS=0x...          # From Step 1
AGENT_WALLET_ADDRESS=0xD8a6beB35E3516338dcFF641538d3984C353E503
AGENT_PRIVATE_KEY=3d7af466e369caae29aee05100731c8800ddd3ab10ddaa5d2f03a1b06aab7273
GEMINI_API_KEY=AIzaSyBsPDY16KUF4UTVS7ZcmtflT_F-rA5zypg
TELEGRAM_BOT_TOKEN=8650450273:AAHib-U-a8abonUeSOxLYf-aMKSxRaTpALk
TELEGRAM_CHAT_ID=5067554737
```

### 2.2 Push to GitHub

```bash
cd /Users/ayomisco/Documents/Main/Hackathons/SYNTHESIS\ Hack/escrova

git add .env contracts/src/ agent/ frontend/
git commit -m "chore: add env vars and update contract address"
git push origin main
```

### 2.3 Connect to Railway

1. Go to **Railway** → **New Project** → **Deploy from GitHub**
2. Select your `-Escrova` repository
3. Railway auto-detects `railway.json` and starts build
4. Wait for "✓ Deployment Successful"
5. Go to **Variables** tab and add all `.env` vars (or Railway auto-reads from repo)

**Check agent is running**:
- Click **Deployments** → **View Logs**
- You should see: `Escrova starting...` and `Escrova monitoring cycle...` every 5 minutes

## 🚀 Step 3: Deploy Frontend to Vercel (5 minutes)

```bash
cd /Users/ayomisco/Documents/Main/Hackathons/SYNTHESIS\ Hack/escrova/frontend

# Install Vercel CLI if needed
npm install -g vercel

# Deploy
vercel --prod
```

### 3.1 Set Vercel Environment Variables

In **Vercel Dashboard** → **Settings** → **Environment Variables**:

```
NEXT_PUBLIC_ESCROVA_CONTRACT=0x...          # From Step 1
NEXT_PUBLIC_CUSD_ALFAJORES=0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1
```

**Your frontend is now live!**
- Production URL: `https://escrova-[random].vercel.app`

## ✅ Step 4: Test Everything (5 minutes)

### 4.1 Test Smart Contract

```bash
# Check contract on Celoscan
# Visit: https://alfajores.celoscan.io/address/0x...
```

### 4.2 Test Agent

```bash
# Check Railway logs
# Should see: "Escrova monitoring cycle..." every 5 minutes
```

### 4.3 Test Frontend

1. Go to `https://escrova-[random].vercel.app`
2. Click **Connect Wallet**
3. Connect MetaMask (Celo Alfajores)
4. Fill out Create Escrow form
5. Click **Create** → MetaMask approval × 2
6. Watch for transaction on **Celoscan**

### 4.4 Test Agent Arbitration

1. Go to escrow detail page
2. Submit a delivery (use any IPFS hash or URL)
3. Raise a dispute
4. Watch **Railway logs** for agent arbitration
5. Check **Celoscan** for `resolveDispute()` transaction

## 🎯 Step 5: Record Demo (10 minutes)

Use **Loom** (https://loom.com):

1. **Intro** (0-15s): "Escrova — AI arbitration for escrow"
2. **Create** (15-45s): Show form, approve, transaction
3. **Dispute** (45-75s): Submit delivery, raise dispute
4. **Arbitrate** (75-110s): Show Railway logs, agent decision
5. **Result** (110-120s): Show on-chain resolution

**Save Loom link**: `https://loom.com/share/YOUR_ID`

## 📋 Step 6: Gather Synthesis Keys (5 minutes)

You need keys from YieldMind and Delegata projects for the same team:

```bash
# From your YieldMind project:
SYNTHESIS_API_KEY=sk-synth-...
SYNTHESIS_TEAM_ID=...
SYNTHESIS_PARTICIPANT_ID=...

# These should be the SAME across all 3 projects
```

If you don't have these, get them from:
- YieldMind GitHub repo or `.env` file
- Delegata GitHub repo or `.env` file

## 🎉 Step 7: Submit to Synthesis (5 minutes)

See `SYNTHESIS_SUBMISSION.md` for detailed API submission.

Quick version:

```bash
# Get track UUIDs
curl https://synthesis.devfolio.co/catalog?page=1&limit=50 | python3 -m json.tool

# Submit project
curl -X POST https://synthesis.devfolio.co/projects \
  -H "Authorization: Bearer YOUR_SYNTHESIS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "teamUUID": "YOUR_TEAM_ID",
    "name": "Escrova",
    "description": "AI-arbitrated escrow on Celo. Autonomous agent evaluates work delivery vs criteria, executes binding on-chain verdicts stored forever.",
    "repoURL": "https://github.com/Ayomisco/-Escrova",
    "trackUUIDs": ["CELO_UUID", "MOONPAY_UUID", "OPENSERV_UUID", "OLAS_UUID", "SYNTHESIS_OPEN_UUID"],
    "deployedURL": "https://escrova-[random].vercel.app",
    "videoURL": "https://loom.com/share/YOUR_VIDEO_ID",
    "submissionMetadata": {
      "agentFramework": "langchain",
      "agentHarness": "claude-code",
      "model": "gemini-2.0-flash"
    }
  }'
```

Response will include `projectUUID`. Save it.

```bash
# Publish
curl -X POST https://synthesis.devfolio.co/projects/$PROJECT_UUID/publish \
  -H "Authorization: Bearer YOUR_SYNTHESIS_API_KEY"
```

## 🎊 Success!

You should now have:

✅ Smart contract deployed on Celo Alfajores
✅ Agent running on Railway (monitoring every 5 min)
✅ Frontend live on Vercel
✅ Demo recorded on Loom
✅ Project submitted to Synthesis

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| Contract deployment fails | Ensure deployer wallet has testnet CELO. Get from faucet.celo.org |
| Agent not starting on Railway | Check env vars are all set. Check logs for Python errors. |
| Frontend shows "not connected" | Switch MetaMask to Celo Alfajores network. Add chain if missing. |
| Agent not detecting disputes | Wait 5 minutes for monitoring cycle. Check Railway logs. |
| Vercel build fails | Run `npm install` locally first. Check for TypeScript errors. |

## 📞 Support Links

- Celo docs: https://docs.celo.org/
- Foundry: https://book.getfoundry.sh/
- Railway: https://docs.railway.app/
- Vercel: https://vercel.com/docs
- Gemini: https://ai.google.dev/
- LangChain: https://python.langchain.com/

---

## Next: Mainnet Deployment (optional)

When ready for mainnet:

1. Change RPC: `--rpc-url https://forno.celo.org`
2. Use mainnet cUSD: `0x765DE816845861e75A25fCA122bb6898B8B1282a`
3. Update all env vars to mainnet endpoints
4. Redeploy to Railway + Vercel

---

**Total time: ~30 minutes from start to live deployment.**

**Go win the hackathon! 🚀**
