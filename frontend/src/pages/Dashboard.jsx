import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'

const ICONS = {
  layers: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M20 7l-8-4-8 4m0 0l8 4m-8-4v10l8 4m0-10l8-4m-8 4v10l8-4" />,
  tag: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />,
  link: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.658 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />,
  grid: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />,
  sync: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />,
  list: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />,
  tree: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />,
  download: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
}
const Icon = ({ name, className }) => <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">{ICONS[name]}</svg>

export default function Dashboard({ stats, onSync }) {
  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState(null)
  const [lastSync, setLastSync] = useState(null)
  const [error, setError] = useState(null)
  const pollRef = useRef(null)

  useEffect(() => {
    fetchLastSync()
    checkSyncStatus()
    return () => clearInterval(pollRef.current)
  }, [])

  const fetchLastSync = async () => {
    try {
      const res = await axios.get('/api/sync/logs?per_page=1')
      if (res.data.data.length > 0) setLastSync(res.data.data[0])
    } catch {}
  }

  const checkSyncStatus = async () => {
    try {
      const res = await axios.get('/api/sync/status')
      if (res.data.running) {
        setSyncing(true)
        startPolling()
      }
    } catch {}
  }

  const startPolling = () => {
    clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const res = await axios.get('/api/sync/status')
        if (!res.data.running) {
          clearInterval(pollRef.current)
          setSyncing(false)
          const last = res.data.last_sync
          setLastSync(last)
          if (last?.status === 'success') {
            setSyncResult(last)
            onSync()
          } else if (last?.status === 'error') {
            setError(last.error_message || 'Error en la sincronización')
          }
        }
      } catch {}
    }, 2000)
  }

  const handleSync = async () => {
    setError(null)
    setSyncResult(null)
    try {
      await axios.post('/api/sync')
      setSyncing(true)
      startPolling()
    } catch (err) {
      if (err.response?.status === 409) {
        setError('Ya hay una sincronización en curso')
        setSyncing(true)
        startPolling()
      } else {
        setError(err.response?.data?.message || 'Error al iniciar sincronización')
      }
    }
  }

  const statCards = [
    { label: 'Total de Activos', value: stats.total_assets || 0, icon: 'layers', accent: 'var(--ferco-navy)', tint: '#eaeaf7' },
    { label: 'Tipos de Activos', value: stats.total_types || 0, icon: 'tag', accent: 'var(--ferco-teal)', tint: '#e5f6f5' },
    { label: 'Relaciones', value: stats.total_relations || 0, icon: 'link', accent: 'var(--ferco-blue)', tint: '#e5f1f8' }
  ]

  return (
    <div className="dash fade-in">
      <div className="dash-hero">
        <div className="dash-hero-inner">
          <div className="dash-hero-icon"><Icon name="grid" /></div>
          <div>
            <h1>Ferco Medical</h1>
            <p>Sistema de Gestión de Activos de TI</p>
          </div>
        </div>
      </div>

      <div className="dash-stats">
        {statCards.map(({ label, value, icon, accent, tint }) => (
          <div key={label} className="stat-card" style={{ '--accent': accent, '--tint': tint }}>
            <div className="stat-card-row">
              <div>
                <p className="stat-card-label">{label}</p>
                <p className="stat-card-value">{value.toLocaleString()}</p>
              </div>
              <div className="stat-card-icon"><Icon name={icon} /></div>
            </div>
          </div>
        ))}
      </div>

      <div className="dash-card">
        <h2>Sincronización con Jira Assets</h2>

        {error && <div className="dash-alert dash-alert-error"><span><strong>Error:</strong> {error}</span></div>}

        {syncResult && (
          <div className="dash-alert dash-alert-success">
            <span><strong>Sincronización completada.</strong> {syncResult.total_assets} activos procesados · {syncResult.total_relations} relaciones · {syncResult.duration_seconds?.toFixed(1)}s</span>
          </div>
        )}

        {lastSync && !syncResult && (
          <div className="dash-lastsync">
            <span><b>Última sincronización:</b> {new Date(lastSync.sync_date).toLocaleString('es-MX')}</span>
            {lastSync.status === 'success' && <span className="ok">{lastSync.total_assets} activos · {lastSync.total_relations} relaciones · {lastSync.duration_seconds?.toFixed(1)}s</span>}
            {lastSync.status === 'error' && <span className="fail">{lastSync.error_message}</span>}
          </div>
        )}

        <div className="dash-sync-row">
          <button onClick={handleSync} disabled={syncing} className="btn-primary">
            <Icon name="sync" className={syncing ? 'spin' : ''} />
            {syncing ? 'Sincronizando…' : 'Sincronizar con Jira'}
          </button>
          {syncing && <p className="dash-sync-note">Procesando activos en segundo plano…</p>}
        </div>
      </div>

      <div className="dash-links">
        <Link to="/assets" className="quick-card" style={{ '--accent': 'var(--ferco-teal)', '--tint': '#e5f6f5' }}>
          <div className="quick-card-icon"><Icon name="list" /></div>
          <h3>Ver Activos</h3>
          <p>Lista completa con búsqueda y filtros</p>
          <span className="quick-cta">Ir a Activos →</span>
        </Link>

        <Link to="/hierarchy" className="quick-card" style={{ '--accent': 'var(--ferco-navy)', '--tint': '#eaeaf7' }}>
          <div className="quick-card-icon"><Icon name="tree" /></div>
          <h3>Jerarquía</h3>
          <p>Árbol de relaciones entre activos</p>
          <span className="quick-cta">Ver Jerarquía →</span>
        </Link>

        <a href="/api/assets/export/csv" className="quick-card" download style={{ '--accent': 'var(--ferco-blue)', '--tint': '#e5f1f8' }}>
          <div className="quick-card-icon"><Icon name="download" /></div>
          <h3>Exportar CSV</h3>
          <p>Descarga todos los activos en CSV</p>
          <span className="quick-cta">Descargar →</span>
        </a>
      </div>
    </div>
  )
}
