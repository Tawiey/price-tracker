import { useState } from 'react'
import fs from 'fs'
import path from 'path'
import Head from 'next/head'
import dynamic from 'next/dynamic'

const PriceChart = dynamic(() => import('../components/PriceChart'), { ssr: false })

export async function getStaticProps() {
  const filePath = path.join(process.cwd(), 'data', 'prices.json')
  let pricesData = { last_updated: null, scrape_count: 0, products: [] }
  try {
    if (fs.existsSync(filePath)) {
      pricesData = JSON.parse(fs.readFileSync(filePath, 'utf8'))
    }
  } catch (e) {
    console.error('Failed to read prices.json:', e)
  }
  return { props: { pricesData } }
}

function dealInfo(history) {
  if (!history?.length) return { current: 0, min: 0, abovePct: 0 }
  const prices = history.map((h) => h.price)
  const current = prices[prices.length - 1]
  const min = Math.min(...prices)
  const abovePct = min > 0 ? ((current - min) / min) * 100 : 0
  return { current, min, abovePct }
}

function fmt(n) {
  return `R${Math.round(n).toLocaleString('en-ZA')}`
}

export default function Home({ pricesData }) {
  const [chartProduct, setChartProduct] = useState(null)
  const { last_updated, scrape_count, products } = pricesData

  const sorted = [...products].sort((a, b) => {
    return dealInfo(a.history).current - dealInfo(b.history).current
  })

  return (
    <>
      <Head>
        <title>65&quot; TV Price Tracker</title>
        <meta name="description" content="Track 65 inch 4K TV prices on Takealot and Amazon South Africa" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased">
        <div className="max-w-6xl mx-auto px-4 py-10">

          {/* Header */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-10">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">65&quot; TV Price Tracker</h1>
              <p className="text-slate-400 mt-1 text-sm">
                Tracking 4K &amp; Neo OLED TVs under R15,000 &middot; Takealot &amp; Amazon SA
              </p>
            </div>
            <div className="flex items-center gap-3">
              {last_updated && (
                <span className="text-slate-500 text-sm">Updated {last_updated}</span>
              )}
              <span className="border border-slate-700 rounded-lg px-3 py-2 text-slate-400 text-xs">
                Auto-scrapes 1st of each month
              </span>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            {[
              { label: 'Products', value: products.length },
              { label: 'Scrape runs', value: scrape_count },
              { label: 'Budget', value: 'R15,000' },
              { label: 'Stores', value: 2 },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">{label}</p>
                <p className="text-2xl font-bold">{value}</p>
              </div>
            ))}
          </div>

          {/* Best price banner */}
          {sorted.length > 0 && (() => {
            const { current, min } = dealInfo(sorted[0].history)
            return current <= min ? (
              <div className="bg-green-900/30 border border-green-700 rounded-xl px-5 py-3 mb-6 text-sm">
                <span className="text-green-400 font-semibold">Lowest price right now</span>
                <span className="text-slate-400 ml-2">— worth buying!</span>
              </div>
            ) : null
          })()}

          {/* Table */}
          {sorted.length > 0 ? (
            <>
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-800">
                  <h2 className="font-semibold text-slate-200">Current Prices</h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Click any row to view the product on the store
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                        <th className="text-left px-6 py-3 font-medium">Store</th>
                        <th className="text-left px-6 py-3 font-medium">Product</th>
                        <th className="text-right px-6 py-3 font-medium">Price</th>
                        <th className="text-right px-6 py-3 font-medium">Lowest ever</th>
                        <th className="text-center px-6 py-3 font-medium">vs Low</th>
                        <th className="text-center px-6 py-3 font-medium">History</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sorted.map((product, i) => {
                        const { current, min, abovePct } = dealInfo(product.history)
                        const priceColor =
                          abovePct <= 1
                            ? 'text-green-400'
                            : abovePct <= 10
                            ? 'text-yellow-400'
                            : 'text-red-400'

                        return (
                          <tr
                            key={i}
                            className={`border-b border-slate-800/60 hover:bg-slate-800/50 transition-colors ${
                              product.url ? 'cursor-pointer' : ''
                            }`}
                            onClick={() => product.url && window.open(product.url, '_blank')}
                          >
                            <td className="px-6 py-4 whitespace-nowrap">
                              {product.store === 'Takealot' ? (
                                <span className="bg-red-950 text-red-300 border border-red-800 text-xs font-medium px-2 py-0.5 rounded">
                                  Takealot
                                </span>
                              ) : (
                                <span className="bg-amber-950 text-amber-300 border border-amber-800 text-xs font-medium px-2 py-0.5 rounded">
                                  Amazon
                                </span>
                              )}
                            </td>
                            <td className="px-6 py-4">
                              <p className="text-slate-100 font-medium leading-snug">
                                {product.title.length > 70
                                  ? product.title.slice(0, 70) + '…'
                                  : product.title}
                              </p>
                              <p className="text-slate-500 text-xs mt-0.5">
                                ZAR &middot; {product.history.length} data point
                                {product.history.length !== 1 ? 's' : ''}
                              </p>
                            </td>
                            <td className="px-6 py-4 text-right whitespace-nowrap">
                              <span className={`font-bold text-base ${priceColor}`}>
                                {fmt(current)}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-right text-slate-300 whitespace-nowrap">
                              {fmt(min)}
                            </td>
                            <td className="px-6 py-4 text-center whitespace-nowrap">
                              {abovePct <= 1 ? (
                                <span className="text-green-400 font-medium text-xs">
                                  &#x25B2; Best price!
                                </span>
                              ) : (
                                <span
                                  className={`text-xs ${
                                    abovePct <= 10 ? 'text-yellow-400' : 'text-slate-500'
                                  }`}
                                >
                                  +{abovePct.toFixed(1)}%
                                </span>
                              )}
                            </td>
                            <td
                              className="px-6 py-4 text-center"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <button
                                onClick={() => setChartProduct(product)}
                                className="text-slate-400 hover:text-blue-400 text-xs px-2 py-1 border border-slate-700 hover:border-blue-600 rounded transition-colors"
                              >
                                Chart
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
              <p className="text-slate-600 text-xs mt-4 text-center">
                Click any row to view the product on Takealot or Amazon South Africa. All prices in ZAR.
              </p>
            </>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-16 text-center">
              <p className="text-5xl mb-4">📺</p>
              <p className="text-xl font-semibold text-slate-200 mb-2">No prices tracked yet</p>
              <p className="text-slate-400">
                Prices will appear here after the first monthly scrape runs via GitHub Actions.
              </p>
            </div>
          )}

        </div>
      </div>

      {chartProduct && (
        <PriceChart product={chartProduct} onClose={() => setChartProduct(null)} />
      )}
    </>
  )
}
