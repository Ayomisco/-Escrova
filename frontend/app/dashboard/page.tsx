'use client'

import Link from 'next/link'

export default function Dashboard() {
  // In a real implementation, fetch escrows for the connected wallet here

  const escrows = [
    {
      id: 1,
      status: 'FUNDED',
      amount: 10,
      criteria: 'Deliver a 500-word article about Ethereum',
      deadline: '2 hours',
      buyer: '0x1234...abcd',
      seller: '0x5678...efgh',
    },
    {
      id: 2,
      status: 'COMPLETED',
      amount: 50,
      criteria: 'Design a logo',
      deadline: '5 days',
      buyer: '0x9999...aaaa',
      seller: '0x1234...abcd',
    },
  ]

  return (
    <div className="min-h-screen px-4 py-12">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">My Escrows</h1>

        <div className="bg-slate-700/50 border border-slate-600 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-600 bg-slate-800/50">
                  <th className="px-6 py-3 text-left text-sm font-semibold">ID</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold">Status</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold">Amount</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold">Criteria</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold">Deadline</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {escrows.map((escrow) => (
                  <tr key={escrow.id} className="border-b border-slate-600 hover:bg-slate-700/30">
                    <td className="px-6 py-4 text-sm">#{escrow.id}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        escrow.status === 'FUNDED' ? 'bg-blue-900/50 text-blue-300' :
                        escrow.status === 'COMPLETED' ? 'bg-green-900/50 text-green-300' :
                        'bg-yellow-900/50 text-yellow-300'
                      }`}>
                        {escrow.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold">{escrow.amount} cUSD</td>
                    <td className="px-6 py-4 text-sm truncate max-w-xs">{escrow.criteria}</td>
                    <td className="px-6 py-4 text-sm text-slate-400">{escrow.deadline}</td>
                    <td className="px-6 py-4 text-sm">
                      <Link href={`/escrow/${escrow.id}`} className="text-cyan-400 hover:text-cyan-300">
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {escrows.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <p className="mb-4">No escrows found</p>
            <Link href="/" className="text-cyan-400 hover:text-cyan-300">
              Create your first escrow →
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
