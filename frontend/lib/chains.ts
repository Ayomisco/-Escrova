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
// This is the unique Celo feature - highlight it in the demo
