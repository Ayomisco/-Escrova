export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 py-12">
      <div className="max-w-2xl mx-auto text-center">
        <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
          Escrova
        </h1>

        <p className="text-2xl text-slate-300 mb-8">
          AI-Arbitrated Escrow on Celo
        </p>

        <p className="text-lg text-slate-400 mb-12 leading-relaxed">
          Trustless escrow for the agentic economy. Hold cUSD, monitor completion criteria,
          release payment automatically, and arbitrate disputes with AI reasoning.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-6">
            <div className="text-3xl mb-3">🔐</div>
            <h3 className="text-lg font-semibold mb-2">Trustless</h3>
            <p className="text-slate-400">No human arbitrator. AI decides disputes.</p>
          </div>

          <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-6">
            <div className="text-3xl mb-3">💰</div>
            <h3 className="text-lg font-semibold mb-2">cUSD Native</h3>
            <p className="text-slate-400">Gas paid in stablecoins. No CELO needed.</p>
          </div>

          <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-6">
            <div className="text-3xl mb-3">⚡</div>
            <h3 className="text-lg font-semibold mb-2">Micro-Escrows</h3>
            <p className="text-slate-400">Gas costs ~$0.001. Small deals viable.</p>
          </div>
        </div>

        <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-8 mb-8">
          <h2 className="text-xl font-semibold mb-4">How It Works</h2>
          <div className="space-y-4 text-left text-slate-300">
            <div className="flex gap-4">
              <span className="text-2xl">1️⃣</span>
              <p><strong>Buyer</strong> creates escrow with criteria + deadline + seller address</p>
            </div>
            <div className="flex gap-4">
              <span className="text-2xl">2️⃣</span>
              <p><strong>Buyer</strong> deposits cUSD (approved first)</p>
            </div>
            <div className="flex gap-4">
              <span className="text-2xl">3️⃣</span>
              <p><strong>Seller</strong> delivers work → submits delivery hash</p>
            </div>
            <div className="flex gap-4">
              <span className="text-2xl">4️⃣</span>
              <p><strong>Buyer confirms</strong> OR <strong>raises dispute</strong></p>
            </div>
            <div className="flex gap-4">
              <span className="text-2xl">⚖️</span>
              <p><strong>Escrova agent</strong> arbitrates with Claude, resolves on-chain</p>
            </div>
          </div>
        </div>

        <button className="bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-500 hover:to-blue-600 text-slate-900 font-bold py-3 px-8 rounded-lg transition">
          Connect Wallet & Create Escrow
        </button>

        <p className="text-slate-500 text-sm mt-8">
          Network: <strong>Celo Alfajores Testnet</strong> |
          Get testnet cUSD at{' '}
          <a href="https://faucet.celo.org/alfajores" className="text-cyan-400 hover:underline">
            faucet.celo.org
          </a>
        </p>
      </div>
    </div>
  )
}
