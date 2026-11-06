import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import logo from '../../img/Ferco-logo.png'
import CreateAssetModal from './CreateAssetModal'
import SearchBox from './SearchBox'

export default function Navbar({ stats, user, onLogout, onAssetCreated }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [showCreate, setShowCreate] = useState(false)
  // Elegir una sugerencia abre el objeto en la vista dividida de su tipo (lista + detalle).
  const openAsset = (asset) => navigate(`/assets?type=${asset.type_id}&object=${asset.id}`)
  const searchAll = (query) => navigate(query ? `/assets?search=${encodeURIComponent(query)}` : '/assets')
  const itemClass = (path) => `app-nav-item ${location.pathname === path ? 'app-nav-item-active' : ''}`
  const selectedTypeId = location.pathname === '/assets' ? new URLSearchParams(location.search).get('type') : ''
  return (
    <>
      <header className="app-header">
        <Link to="/assets" className="app-brand" aria-label="Ir a activos"><img src={logo} alt="Ferco Medical" /><span>Assets</span></Link>
        <SearchBox className="app-search" placeholder="Buscar activos, claves, usuarios, DNI o N° de serie" onSelect={openAsset} onSubmit={searchAll} />
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
