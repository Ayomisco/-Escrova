# Escrova Demo Script

## Setup
- **Network**: Celo Alfajores Testnet
- **Frontend**: http://localhost:3000
- **Agent logs**: Railway dashboard or local terminal
- **Explorer**: https://alfajores.celoscan.io

---

## Demo Flow (2 minutes)

### 1. Show the Frontend
**Narration**: "Two parties, one escrow. No trust required. Let me show you Escrova in action."

- Open http://localhost:3000
- Show the landing page: features, how it works, call-to-action

### 2. Create an Escrow
**Narration**: "A buyer wants to hire a seller. They don't know each other. They need trust."

**Steps**:
1. Click "Connect Wallet & Create Escrow"
2. Connect MetaMask (switch to Celo Alfajores testnet)
3. Fill the form:
   - **Seller Address**: 0x[seller_address]
   - **Amount**: 10 cUSD
   - **Deadline**: 1 hour from now
   - **Criteria**: "Deliver a 500-word article about Ethereum and sign it"
4. Click Create
5. MetaMask pops up twice:
   - First: Approve cUSD for the contract
   - Second: Execute createAndFund()
6. Show transaction on Celoscan: https://alfajores.celoscan.io/tx/[TXHASH]

### 3. Seller Submits Delivery
**Narration**: "The seller completes the work and submits proof."

**Steps**:
1. Switch to seller's MetaMask account
2. Go to Escrow detail page (/escrow/1)
3. Upload a test file to IPFS (https://ipfs.io):
   - Create a simple text file or upload existing content
   - Get the IPFS hash: QmXxxx...
4. Paste the IPFS hash in "Submit Delivery" field
5. Click Submit
6. Show transaction confirmed on Celoscan

### 4. Raise a Dispute
**Narration**: "The buyer reviews the delivery and decides it doesn't meet the criteria."

**Steps**:
1. Switch to buyer's MetaMask account
2. Go to Escrow detail page
3. Click "Raise Dispute"
4. Show status changed to DISPUTED on Celoscan

### 5. Show Agent Arbitration (Railway Logs)
**Narration**: "Behind the scenes, the Escrova agent is monitoring. When it detects a dispute, it springs into action."

**Show Railway/Local Logs**:
```
[Agent]: Escrova monitoring cycle...
[Agent]: Scanning all escrows...
[Agent]: Found 1 disputed escrow.
[Agent]: Fetching delivery content from IPFS...
[Agent]: Evaluating criteria vs delivery...
[Agent]: Reasoning: "Criteria required 500 words. Delivery contains 312 words. Criteria not met. Buyer wins."
[Agent]: Calling arbitrate_dispute(escrow_id=1, sellerWins=false)
[Agent]: Transaction submitted: 0x[TXHASH]
[Agent]: Dispute resolved on-chain.
```

### 6. Show On-Chain Resolution
**Narration**: "The verdict is final. The reasoning is stored on-chain. The payment is released automatically."

**Steps**:
1. Go to Celoscan
2. Find the resolveDispute() transaction
3. Click on it
4. Show the "reasoning" parameter in the input data:
   ```
   reasoning: "Criteria required 500 words. Delivery contains 312 words. Criteria not met. Buyer wins."
   ```
5. Show cUSD transferred:
   - Buyer receives 10 cUSD (full amount back)
   - Agent receives 0.1 cUSD (1% platform fee)

### 7. Show Telegram Alert
**Narration**: "The operator gets a notification."

**Show Terminal/Telegram**:
```
[Escrova] Dispute resolved. Buyer wins.
Reason: Criteria required 500 words. Delivery contains 312 words. Criteria not met.
Transaction: https://alfajores.celoscan.io/tx/0x...
```

### 8. Show Agent Earnings
**Narration**: "The agent is economically self-sustaining. It earns 1% of every escrow it arbitrates."

**Show Agent Output**:
```
[Agent]: Agent wallet: 0x...
[Agent]: Current balance: 0.10 cUSD
[Agent]: Total earned from fees: 0.10 cUSD
```

---

## Key Talking Points

1. **No Human Arbitrator**: The AI evaluated the work fairly and executed the verdict on-chain in 30 seconds.

2. **Reasoning On-Chain**: The arbitration reasoning is stored permanently in the transaction. Anyone can verify the decision.

3. **Gas Paid in Stablecoins**: This is unique to Celo. The agent never needs a native token. Gas costs ~$0.001 per transaction.

4. **Self-Sustaining Agent**: The agent earns 1% platform fees. Over time, these fees fund its operations. True autonomy.

5. **Works Globally**: No banks, no jurisdictions, no KYC. Two parties, any blockchain address, any language.

6. **Micro-Escrows Viable**: For the first time, a $1 escrow is economically viable. Gas costs are negligible.

---

## Common Questions

**Q: How does the agent know what's fair?**
A: Claude evaluates the plain-text criteria and the actual delivery. It applies common sense and legal reasoning. Any dispute is resolved transparently with reasoning stored on-chain.

**Q: What if the agent is wrong?**
A: The reasoning is visible to both parties. If the agent consistently makes bad decisions, its reputation suffers and users will stop using Escrova. Economic incentives align with fairness.

**Q: Can either party appeal?**
A: In this MVP, the arbiter is final. Future versions could implement a reputation system and multi-level arbitration.

**Q: How is the agent paid?**
A: Through 1% platform fees. Over time, these fees sustain the agent's compute costs on Celo.

---

## Troubleshooting

- **MetaMask rejection**: Make sure you're on Celo Alfajores testnet
- **Transaction fails**: Check that you have testnet CELO for gas (get from faucet.celo.org)
- **Agent not detecting dispute**: Make sure Railway service is running. Check env vars.
- **IPFS hash not fetching**: Use a valid IPFS hash or URL. The agent will log the error.

---

## After the Demo

1. Deploy to Vercel (frontend) and Railway (agent)
2. Submit to Synthesis with track UUIDs for: Celo, MoonPay, OpenServ, Olas, Synthesis Open
3. Share the live links in your submission
