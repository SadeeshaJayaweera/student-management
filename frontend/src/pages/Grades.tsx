import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import { Bar } from 'react-chartjs-2'
import { Chart, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'
import type { GradeRecord } from '@/types'
Chart.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend)

function letterClass(l: string | null) {
  if (!l) return 'badge-warning'
  if (l.startsWith('A')) return 'badge-success'
  if (l.startsWith('B')) return 'badge-info'
  if (l === 'F') return 'badge-danger'
  return 'badge-warning'
}

function GpaRing({ gpa }: { gpa: number }) {
  const r = 65, circ = 2 * Math.PI * r, dash = (gpa / 4) * circ
  return (
    <div className="gpa-ring">
      <svg width="160" height="160" viewBox="0 0 160 160">
        <circle cx="80" cy="80" r={r} fill="none" stroke="rgba(255,255,255,.06)" strokeWidth="12" />
        <circle cx="80" cy="80" r={r} fill="none" stroke="url(#gg)" strokeWidth="12"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" />
        <defs>
          <linearGradient id="gg" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#6C63FF" />
            <stop offset="100%" stopColor="#00D4AA" />
          </linearGradient>
        </defs>
      </svg>
      <div className="gpa-ring-val">{gpa.toFixed(2)}</div>
    </div>
  )
}

export default function Grades() {
  const [grades, setGrades] = useState<GradeRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<GradeRecord[]>('/students/grades')
      .then(r => setGrades(r.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  const totalGP = grades.reduce((s, g) => s + (g.grade_points ?? 0) * (g.credits ?? 3), 0)
  const totalCr = grades.reduce((s, g) => s + (g.credits ?? 3), 0)
  const gpa = totalCr ? totalGP / totalCr : 0

  const gpaClass = gpa >= 3.8 ? { label: "🏆 Dean's List", cls: 'badge-gold' }
    : gpa >= 3.5 ? { label: '🥇 First Class', cls: 'badge-success' }
    : gpa >= 3.0 ? { label: '🥈 Second Upper', cls: 'badge-success' }
    : gpa >= 2.0 ? { label: '✅ Pass', cls: 'badge-info' }
    : { label: '❌ At Risk', cls: 'badge-danger' }

  const gradeLabels = ['A+/A', 'B+/B', 'C+/C', 'D', 'F']
  const gradeCounts = [
    grades.filter(g => g.letter_grade && ['A+', 'A'].includes(g.letter_grade)).length,
    grades.filter(g => g.letter_grade && ['B+', 'B'].includes(g.letter_grade)).length,
    grades.filter(g => g.letter_grade && ['C+', 'C'].includes(g.letter_grade)).length,
    grades.filter(g => g.letter_grade === 'D').length,
    grades.filter(g => g.letter_grade === 'F').length,
  ]

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">📊 Grades & GPA</div>
        <div className="page-subtitle">Academic performance across all courses</div>
      </div>

      <div className="grid-2 mb-24" style={{ gridTemplateColumns: '1fr 2fr' }}>
        {/* GPA Ring */}
        <div className="card flex flex-col items-center justify-center gap-16">
          <GpaRing gpa={gpa} />
          <div style={{ textAlign: 'center' }}>
            <div className="text-sm text-muted">Cumulative GPA</div>
            <span className={`badge ${gpaClass.cls} mt-8`}>{gpaClass.label}</span>
          </div>
          <div style={{ width: '100%', paddingTop: 12, borderTop: '1px solid var(--border)' }}>
            {[
              ['Total Courses', grades.length],
              ['Credits Earned', totalCr],
              ['Grade Points', totalGP.toFixed(1)],
            ].map(([l, v]) => (
              <div key={String(l)} className="flex justify-between text-sm" style={{ padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,.04)' }}>
                <span className="text-muted">{l}</span>
                <span style={{ fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Bar Chart */}
        <div className="card">
          <div className="card-title mb-16">Grade Distribution</div>
          <Bar data={{
            labels: gradeLabels,
            datasets: [{
              data: gradeCounts,
              backgroundColor: ['rgba(0,212,170,.55)', 'rgba(108,99,255,.55)', 'rgba(255,179,71,.55)', 'rgba(255,107,107,.4)', 'rgba(255,50,50,.55)'],
              borderColor: ['#00D4AA', '#6C63FF', '#FFB347', '#FF6B6B', '#FF3232'],
              borderWidth: 2, borderRadius: 8,
            }],
          }} options={{
            responsive: true, plugins: { legend: { display: false } },
            scales: {
              y: { ticks: { color: 'rgba(255,255,255,.4)', stepSize: 1 }, grid: { color: 'rgba(255,255,255,.05)' } },
              x: { ticks: { color: 'rgba(255,255,255,.55)' }, grid: { display: false } },
            },
          }} />
        </div>
      </div>

      {/* Grade Table */}
      <div className="card">
        <div className="card-title mb-16">📋 Grade Report</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Code</th><th>Course</th><th>Credits</th>
                <th>Midterm</th><th>Final</th><th>Assignments</th>
                <th>Total</th><th>Grade</th><th>GP</th>
              </tr>
            </thead>
            <tbody>
              {grades.map(g => {
                const gpc = (g.grade_points ?? 0) >= 3.5 ? '#00D4AA' : (g.grade_points ?? 0) >= 2.5 ? '#8B85FF' : (g.grade_points ?? 0) >= 2 ? '#FFB347' : '#FF6B6B'
                return (
                  <tr key={g.id}>
                    <td><span className="badge badge-info">{g.course_code}</span></td>
                    <td style={{ fontWeight: 600 }}>{g.course_title}</td>
                    <td className="text-muted">{g.credits}</td>
                    <td>{g.midterm != null ? g.midterm.toFixed(1) : '—'}</td>
                    <td>{g.final != null ? g.final.toFixed(1) : '—'}</td>
                    <td>{g.assignments_avg != null ? g.assignments_avg.toFixed(1) : '—'}</td>
                    <td style={{ fontWeight: 700 }}>{g.total != null ? g.total.toFixed(1) : '—'}</td>
                    <td><span className={`badge ${letterClass(g.letter_grade)}`}>{g.letter_grade ?? '—'}</span></td>
                    <td style={{ fontWeight: 700, color: gpc }}>{g.grade_points != null ? g.grade_points.toFixed(1) : '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
