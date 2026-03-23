'use client'

import { useState } from 'react'

export default function EscrowDetail({ params }: { params: { id: string } }) {
  const [deliveryHash, setDeliveryHash] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // In a real implementation, fetch escrow data and handle transactions here

  return (
    <div className="min-h-screen px-4 py-12">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Escrow #{params.id}</h1>
          <p className="text-slate-400">Status: <span className="text-cyan-400 font-semibold">FUNDED</span></p>
        </div>

        <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-8 mb-8">
          <h2 className="text-xl font-semibold mb-4">Details</h2>
          <div className="space-y-4 text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-400">Buyer:</span>
              <code className="text-sm bg-slate-800 px-2 py-1 rounded">0x1234...abcd</code>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Seller:</span>
              <code className="text-sm bg-slate-800 px-2 py-1 rounded">0x5678...efgh</code>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Amount:</span>
              <span className="font-semibold">10 cUSD</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Deadline:</span>
              <span>2 hours from now</span>
            </div>
            <div className="flex justify-between pt-4 border-t border-slate-600">
              <span className="text-slate-400">Criteria:</span>
              <span className="text-right max-w-sm">Deliver a 500-word article about Ethereum and sign it</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-8">
          <h2 className="text-xl font-semibold mb-4">Actions</h2>

          <div className="space-y-4">
            <div className="border-b border-slate-600 pb-4">
              <h3 className="font-semibold mb-2">Seller: Submit Delivery</h3>
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  placeholder="IPFS hash or URL hash"
                  value={deliveryHash}
                  onChange={(e) => setDeliveryHash(e.target.value)}
                  className="flex-1 bg-slate-800 border border-slate-600 rounded px-3 py-2 text-slate-300 placeholder-slate-500"
                />
                <button
                  disabled={isLoading || !deliveryHash}
                  className="bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-600 text-slate-900 font-semibold px-4 py-2 rounded transition"
                >
                  {isLoading ? 'Submitting...' : 'Submit'}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="font-semibold">Buyer: Confirm or Dispute</h3>
              <div className="flex gap-2">
                <button className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 rounded transition">
                  Confirm Complete
                </button>
                <button className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-2 rounded transition">
                  Raise Dispute
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
