import React, { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import logo from '../../img/Ferco-logo.png'
import axios from 'axios'
import CreateAssetModal from './CreateAssetModal'

export default function Navbar({ stats, user, onLogout, onAssetCreated }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  useEffect(() => {
    if (query.trim().length < 2) { setSuggestions([]); return }
    const timeout = setTimeout(() => axios.get('/api/search/suggestions', { params: { q: query } })
      .then(response => setSuggestions(response.data.data)).catch(() => setSuggestions([])), 180)
    return () => clearTimeout(timeout)
  }, [query])
  const search = (event) => {
    event.preventDefault()
    const trimmed = query.trim()
    navigate(trimmed ? `/assets?search=${encodeURIComponent(trimmed)}` : '/assets')
    setShowSuggestions(false)
  }
  const itemClass = (path) => `app-nav-item ${location.pathname === path ? 'app-nav-item-active' : ''}`
  const selectedTypeId = location.pathname === '/assets' ? new URLSearchParams(location.search).get('type') : ''
  return (
    <>
      <header className="app-header">
        <Link to="/assets" className="app-brand" aria-label="Ir a activos"><img src={logo} alt="Ferco Medical" /><span>Assets</span></Link>
        <form className="app-search" onSubmit={search}><span aria-hidden="true">⌕</span><input value={query} onFocus={() => setShowSuggestions(true)} onChange={(e) => { setQuery(e.target.value); setShowSuggestions(true) }} placeholder="Buscar activos, claves o usuarios" />{showSuggestions && suggestions.length > 0 && <div className="global-suggestions">{suggestions.map(asset => <button type="button" key={asset.id} onMouseDown={() => { navigate(`/assets/${asset.id}`); setQuery(''); setShowSuggestions(false) }}><span>{asset.type_name === 'Usuario' ? '👤' : '▣'}</span><span><strong>{asset.name}</strong><small>{asset.type_name} · {asset.jira_key}</small></span></button>)}</div>}</form>
        <button className="app-create" onClick={() => setShowCreate(true)}>＋ Crear</button>
        <button className="app-user" onClick={onLogout} title="Cerrar sesión">{user?.display_name || user?.email} · Salir</button>
      </header>
      <CreateAssetModal open={showCreate} initialTypeId={selectedTypeId} onClose={() => setShowCreate(false)} onCreated={(asset) => { onAssetCreated?.(); navigate(`/assets/${asset.id}`) }} />
      <aside className="app-nav" aria-label="Navegación principal">
        <p className="app-nav-label">NAVEGACIÓN</p>
        <Link to="/" className={itemClass('/')}>▦ <span>Resumen</span></Link>
        <Link to="/assets" className={itemClass('/assets')}>⌘ <span>Esquemas</span></Link>
        <Link to="/hierarchy" className={itemClass('/hierarchy')}>⌘ <span>Relaciones</span></Link>
        <div className="app-nav-divider" />
        <div className="app-nav-info"><strong>{stats.total_assets || 0}</strong> activos locales<br /><span>{stats.total_types || 0} tipos · {stats.total_relations || 0} vínculos</span></div>
      </aside>
    </>
  )
}
