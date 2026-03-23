import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Escrova — AI-Arbitrated Escrow on Celo",
  description: "Trustless escrow for the agentic economy",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <main className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
          {children}
        </main>
      </body>
    </html>
  )
}
