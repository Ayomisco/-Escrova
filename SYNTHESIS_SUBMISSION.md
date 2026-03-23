# Escrova — Synthesis Submission Guide

This guide walks you through submitting Escrova to the Synthesis hackathon.

## Prerequisites

- Completion of deployments (smart contract, agent, frontend)
- Synthesis API key (same as YieldMind and Delegata — you're registering project #3)
- Team UUID (same as YieldMind and Delegata)
- GitHub repository with code pushed
- Loom video of demo (2 minutes)

---

## Step 7.1: Gather Track UUIDs

The Synthesis hackathon has specific tracks. Find the UUIDs for the tracks you're competing in.

```bash
# Fetch the catalog
curl https://synthesis.devfolio.co/catalog?page=1&limit=50 | python3 -m json.tool
```

Look for these tracks and copy their UUIDs:
- **Celo** — Focus on cUSD stablecoin gas, Celo-specific features
- **MoonPay** — Cross-chain on-ramp integration
- **OpenServ** — ERC-8004 agent identity and marketplace
- **Olas** — Agent-to-agent coordination
- **Synthesis Open Track** — General/best project

Save the UUIDs:
```
CELO_TRACK_UUID=...
MOONPAY_TRACK_UUID=...
OPENSERV_TRACK_UUID=...
OLAS_TRACK_UUID=...
SYNTHESIS_OPEN_TRACK_UUID=...
```

---

## Step 7.2: Record Demo Video (2 minutes)

Use Loom (https://loom.com) to record a 2-minute demo:

### Demo Outline
1. **Intro** (0-15s):
   - "This is Escrova — an autonomous AI arbitration agent on Celo."
   - Show the landing page

2. **Create Escrow** (15-45s):
   - Connect wallet
   - Fill form with test data
   - Show transaction on Celoscan

3. **Raise Dispute** (45-75s):
   - Switch accounts, submit delivery
   - Raise dispute
   - Show status: DISPUTED

4. **Agent Arbitrates** (75-110s):
   - Show Railway logs
   - Agent detects dispute
   - Agent evaluates and calls resolveDispute()
   - Show transaction on Celoscan

5. **Result** (110-120s):
   - Show reasoning on-chain
   - Show payment executed
   - Narrate: "AI arbitration, stored on-chain, no middleman."

### Recording Tips
- Use a clear voice
- Show the critical transactions on Celoscan
- Highlight the on-chain reasoning (key differentiator)
- Keep it under 2 minutes

Save the Loom link: `https://loom.com/share/YOUR_VIDEO_ID`

---

## Step 7.3: Create Project via API

The Synthesis hackathon uses a REST API to submit projects. You're using the same API key and team as YieldMind/Delegata.

### Build the submission JSON

```bash
cat > /tmp/escrova_submission.json << 'EOF'
{
  "teamUUID": "YOUR_SAME_TEAM_ID",
  "name": "Escrova",
  "description": "An autonomous AI arbitration agent on Celo. Escrova holds cUSD in trustless escrow, monitors work delivery, and resolves disputes on-chain with AI reasoning — stored permanently in the transaction. No human middleman. Gas paid in cUSD (Celo's unique stablecoin fee feature). Earns 1% platform fees to sustain agent operations. Works for human-to-human, human-to-agent, and agent-to-agent transactions globally.",

  "problemStatement": "When two parties exchange value for work, someone has to go first. Traditional escrow requires a trusted human arbitrator — expensive, slow, jurisdiction-dependent. AI agents trading services with each other have no trustless payment mechanism at all. The agentic economy needs an autonomous arbitration layer: one that evaluates work criteria against actual deliveries, executes binding verdicts on-chain, and stores its reasoning transparently. No banks. No lawyers. No middlemen. Just code and AI.",

  "repoURL": "https://github.com/YOUR_USERNAME/escrova",

  "trackUUIDs": [
    "CELO_TRACK_UUID",
    "MOONPAY_TRACK_UUID",
    "OPENSERV_TRACK_UUID",
    "OLAS_TRACK_UUID",
    "SYNTHESIS_OPEN_TRACK_UUID"
  ],

  "deployedURL": "https://escrova-[random].vercel.app",
  "videoURL": "https://loom.com/share/YOUR_VIDEO_ID",

  "conversationLog": "Built ESCROVA with Claude Code. Started by identifying the core problem: no trustless arbitration for agent-to-agent payments. Chose Celo for stablecoin-native gas (agents pay in cUSD, no native token needed). Wrote EscrovaVault.sol with 6 escrow states: OPEN→FUNDED→COMPLETED|DISPUTED→RESOLVED|REFUNDED. Key design: 1% platform fee to self-fund agent operations. LangGraph agent monitors contract every 5 min, fetches disputed escrows, reads delivery content from IPFS, evaluates against criteria using Claude, calls resolveDispute() with on-chain reasoning. Added support for cross-chain on-ramps via MoonPay quotes. Registered agent on OpenServ marketplace as ERC-8004 identity. Demo shows full dispute resolution in under 60 seconds.",

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
        "reason": "Confirmed Celo migrated to OP Stack L2 in March 2025 — saved us from deploying to wrong network config"
      },
      {
        "name": "ethskills-security",
        "reason": "Reminded us cUSD uses 18 decimals (not 6 like USDC) — would have been a critical escrow calculation bug"
      }
    ],

    "intention": "continuing",
    "intentionNotes": "Real use case: freelancer marketplaces, DAO grant disbursement, agent-to-agent service payment. Conversations with gig economy platforms about integration."
  }
}
EOF
```

### Submit the project

```bash
# Set your API key and team ID
export SYNTHESIS_API_KEY="sk-synth-..."
export SYNTHESIS_TEAM_ID="your-team-uuid"

# Submit
curl -X POST https://synthesis.devfolio.co/projects \
  -H "Authorization: Bearer $SYNTHESIS_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/escrova_submission.json
```

### Save the response
You'll get back a response with `projectUUID`. Save this:
```bash
export ESCROVA_PROJECT_UUID="..."
```

---

## Step 7.4: Self-Custody Transfer

If you already completed self-custody transfer for YieldMind, you're done here. The self-custody proof applies to your entire team.

If not, Synthesis will send you instructions to:
1. Sign a message with your wallet
2. Prove control of the addresses listed in your submission

---

## Step 7.5: Publish Your Project

Once your project is created and (if needed) self-custody is verified:

```bash
curl -X POST https://synthesis.devfolio.co/projects/$ESCROVA_PROJECT_UUID/publish \
  -H "Authorization: Bearer $SYNTHESIS_API_KEY"
```

Your project is now **live** and visible to judges.

---

## Submission Checklist

- [ ] Contract deployed to Celo Alfajores (save address)
- [ ] Agent deployed to Railway (verify logs show it's running)
- [ ] Frontend deployed to Vercel (verify it loads)
- [ ] Demo recorded on Loom (2 minutes, under 120 seconds)
- [ ] GitHub repo pushed with all code
- [ ] Track UUIDs found and saved
- [ ] Submission JSON created with correct URLs and metadata
- [ ] Project submitted via API (save project UUID)
- [ ] Self-custody verified (if needed)
- [ ] Project published

---

## Submission Highlights (for judges)

When judges evaluate Escrova, emphasize:

### Innovation
- **First autonomous arbitrator for the agentic economy** — No existing system trusts AI for dispute resolution
- **Celo-native design** — Only viable because cUSD gas allows micro-escrows
- **Self-sustaining agent** — Fees fund operations, no external funding needed

### Technical
- **6-state escrow FSM** — Clean state management (OPEN→FUNDED→COMPLETED|DISPUTED→RESOLVED|REFUNDED)
- **On-chain reasoning** — Arbitration logic stored permanently, auditable, verifiable
- **LangGraph + Foundry** — Modern tooling combining Web3 and AI
- **Real integration** — ERC20, IPFS, on-chain events, Telegram alerts

### Real-World Use
- **Freelancer marketplaces** — No escrow service exists that's decentralized + arbitrated
- **DAO grants** — Trustless milestone-based disbursement
- **Agent-to-agent payments** — Unique to agentic economy

### Risk Mitigation
- **Security** — ReentrancyGuard, SafeERC20, no math overflow, arbiter role-based
- **Fault tolerance** — Agent retries, Telegram alerts on error
- **Testnet proof** — Full end-to-end demo on Celo Alfajores

---

## FAQ

**Q: Can I submit to multiple tracks?**
A: Yes — include all relevant track UUIDs in trackUUIDs array.

**Q: What if my agent fails?**
A: Submit anyway. Your code demonstrates the architecture. Judges care about approach + execution.

**Q: How do judges verify the agent works?**
A: They'll watch your Loom demo and check Railway logs. Real arbitration = proof of execution.

**Q: Should I deploy to mainnet before submitting?**
A: Not required. Testnet is fine. Mainnet shows confidence but isn't necessary.

**Q: How long until judges evaluate?**
A: Check Synthesis timeline. Usually 1-2 weeks after submission deadline.

---

## After Submission

- Monitor Synthesis announcements for winner announcements
- Keep your GitHub repo active — judges may check commit history
- Update your demo video if you find bugs
- Continue development — show momentum

---

## Support

- Synthesis docs: https://synthesis.devfolio.co/docs
- Celo dev docs: https://docs.celo.org/
- For questions: Use Synthesis Discord or contact organizers directly
