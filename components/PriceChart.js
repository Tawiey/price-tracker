import { useEffect, useRef } from 'react'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default function PriceChart({ product, onClose }) {
  const canvasRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    const handleKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  useEffect(() => {
    if (!canvasRef.current || product.history.length < 2) return

    if (chartRef.current) chartRef.current.destroy()

    chartRef.current = new Chart(canvasRef.current, {
      type: 'line',
      data: {
        labels: product.history.map((h) => h.date),
        datasets: [
          {
            data: product.history.map((h) => h.price),
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59,130,246,0.08)',
            fill: true,
            tension: 0.35,
            pointRadius: 5,
            pointHoverRadius: 7,
            pointBackgroundColor: '#3b82f6',
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#1e293b',
            borderColor: '#334155',
            borderWidth: 1,
            titleColor: '#94a3b8',
            bodyColor: '#f1f5f9',
            callbacks: {
              label: (ctx) => ` R${Math.round(ctx.parsed.y).toLocaleString('en-ZA')}`,
            },
          },
        },
        scales: {
          x: {
            ticks: { color: '#64748b', font: { size: 11 } },
            grid: { color: 'rgba(100,116,139,0.15)' },
          },
          y: {
            ticks: {
              color: '#64748b',
              font: { size: 11 },
              callback: (v) => `R${Math.round(v).toLocaleString('en-ZA')}`,
            },
            grid: { color: 'rgba(100,116,139,0.15)' },
          },
        },
      },
    })

    return () => chartRef.current?.destroy()
  }, [product])

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-2xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-5">
          <div>
            <h2 className="font-semibold text-white text-lg leading-tight max-w-lg">
              {product.title}
            </h2>
            <p className="text-slate-400 text-sm mt-0.5">{product.store}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-2xl leading-none ml-4 flex-shrink-0"
          >
            &times;
          </button>
        </div>

        <div className="relative h-64">
          {product.history.length < 2 ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <p className="text-slate-500 text-sm">
                Only one data point — check back after the next scrape.
              </p>
            </div>
          ) : (
            <canvas ref={canvasRef} />
          )}
        </div>
      </div>
    </div>
  )
}
