import React, { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import axios from 'axios'
import AssetDetail from './AssetDetail'
import SearchBox from '../components/SearchBox'

const iconFor = (name = '') => /laptop|all in one/i.test(name) ? '💻' : /celular|móvil|tablet/i.test(name) ? '📱' : /software|office|windows/i.test(name) ? '💿' : /impresora/i.test(name) ? '🖨️' : /usuario/i.test(name) ? '👤' : '▣'

function TreeGroup({ name, icon, types, counts, selectedType, onSelect }) {
  const [open, setOpen] = useState(true)
  const total = types.reduce((sum, type) => sum + (counts[type.id] || 0), 0)
  if (!types.length) return null
  return <div className="schema-group"><button className="schema-node schema-group-title" onClick={() => setOpen(!open)}><span>{open ? '⌄' : '›'}</span><span>{icon}</span><span className="schema-node-name">{name}</span><b>{total}</b></button>{open && types.map(type => <button key={type.id} onClick={() => onSelect(String(type.id))} className={`schema-node schema-child ${selectedType === String(type.id) ? 'schema-node-selected' : ''}`}><span>{iconFor(type.name)}</span><span className="schema-node-name">{type.name}</span><b>{counts[type.id] ?? '…'}</b></button>)}</div>
}

export default function AssetsList() {
  const [assets, setAssets] = useState([])
  const [types, setTypes] = useState([])
  const [counts, setCounts] = useState({})
  const [loading, setLoading] = useState(true)
  const [params, setParams] = useSearchParams()
  const [pagination, setPagination] = useState({ total: 0, page: 1, pages: 1 })
  const [reloadKey, setReloadKey] = useState(0)
  const selectedType = params.get('type') || ''
  // Con un tipo seleccionado se usa la vista dividida estilo Jira (lista de objetos + detalle);
  // ?view=table vuelve a la tabla clásica.
  const splitView = Boolean(selectedType) && params.get('view') !== 'table'
  const perPage = splitView ? 200 : 50
  const selectedObject = params.get('object') || (splitView && assets[0] ? String(assets[0].id) : '')

  useEffect(() => { axios.get('/api/asset-types').then((r) => setTypes(r.data.data)).catch(console.error) }, [])
  useEffect(() => {
    Promise.all(types.map((type) => axios.get('/api/assets', { params: { type_id: type.id, per_page: 1 } })))
      .then((responses) => setCounts(Object.fromEntries(responses.map((r, i) => [types[i].id, r.data.total]))))
      .catch(() => {})
  }, [types])
  useEffect(() => {
    setLoading(true)
    const request = { page: Number(params.get('page') || 1), per_page: perPage }
    if (params.get('search')) request.search = params.get('search')
    if (selectedType) request.type_id = selectedType
    axios.get('/api/assets', { params: request }).then((r) => {
      setAssets(r.data.data); setPagination({ total: r.data.total, page: r.data.page, pages: r.data.pages })
    }).catch(console.error).finally(() => setLoading(false))
  }, [params.get('page'), params.get('search'), selectedType, perPage, reloadKey])

  const selectedName = useMemo(() => types.find((type) => String(type.id) === selectedType)?.name || 'Todos los activos', [types, selectedType])
  const groups = useMemo(() => {
    const hardware = /^(CPU|Laptop|Impresoras|All In One|Celular|Proyectores|Monitor|Almacenamiento|Dispositivos de Red|Tablet|Servidores)$/i
    const software = /office|windows|software|ms 365/i
    const models = /^(Modelo|Marca|Proveedor Móvil|Suite Office|Modelos)$/i
    return {
      hardware: types.filter(t => hardware.test(t.name)),
      software: types.filter(t => software.test(t.name)),
      models: types.filter(t => models.test(t.name)),
      other: types.filter(t => !hardware.test(t.name) && !software.test(t.name) && !models.test(t.name))
    }
  }, [types])
  const change = (next = {}) => {
    const result = new URLSearchParams(params)
    if (('type' in next || 'search' in next) && !('object' in next)) result.delete('object')
    Object.entries(next).forEach(([key, value]) => value ? result.set(key, value) : result.delete(key))
    if (!('page' in next) && !('object' in next)) result.set('page', '1')
    setParams(result)
  }
  const formatDate = (value) => value ? new Intl.DateTimeFormat('es-PE', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value)) : '—'

  return <div className="assets-screen">
    <div className="assets-breadcrumb">Activos <span>/</span> Esquemas</div>
    <div className="assets-titlebar"><h1>Activos de TI</h1><SearchBox className="schema-search" typeId={selectedType} initialValue={params.get('search') || ''} placeholder={selectedType ? `Buscar en ${selectedName}` : 'Buscar en este esquema'} onSelect={item => change({ type: String(item.type_id), object: String(item.id), search: '', view: '', page: '1' })} onSubmit={q => change({ search: q })} onClear={() => change({ search: '' })} /></div>
    <div className="assets-workspace">
      <aside className="schema-tree"><div className="schema-tree-heading">ÁRBOL DEL ESQUEMA <span>＋</span></div><button className={`schema-node schema-root ${!selectedType ? 'schema-node-selected' : ''}`} onClick={() => change({ type: '' })}>⌄ <span>▣</span> Activos de TI <b>{Object.values(counts).reduce((a, b) => a + b, 0)}</b></button>
        <TreeGroup name="Activos de hardware" icon="🖥️" types={groups.hardware} counts={counts} selectedType={selectedType} onSelect={type => change({ type })} />
        <TreeGroup name="Activos de software" icon="💿" types={groups.software} counts={counts} selectedType={selectedType} onSelect={type => change({ type })} />
        <TreeGroup name="Modelos y fabricantes" icon="◉" types={groups.models} counts={counts} selectedType={selectedType} onSelect={type => change({ type })} />
        {groups.other.map(type => <button key={type.id} onClick={() => change({ type: String(type.id) })} className={`schema-node ${selectedType === String(type.id) ? 'schema-node-selected' : ''}`}><span>{iconFor(type.name)}</span><span className="schema-node-name">{type.name}</span><b>{counts[type.id] ?? '…'}</b></button>)}
      </aside>
      <section className="schema-content">
        <div className="schema-content-heading"><div><span className="schema-heading-icon">{iconFor(selectedName)}</span><h2>{selectedName}</h2></div><span className="schema-view-toggle">Objetos</span></div>
        {splitView ? <div className="object-split">
          <div className="object-list-panel">
            <div className="object-list-header"><span>{pagination.total} objetos</span><button title="Ver como tabla" onClick={() => change({ view: 'table', object: '', page: '1' })}>☷</button></div>
            <div className="object-list">{loading ? <div className="asset-empty">Cargando…</div> : assets.length === 0 ? <div className="asset-empty">No se encontraron objetos</div> : assets.map(asset => <button key={asset.id} className={`object-list-item ${selectedObject === String(asset.id) ? 'object-list-item-selected' : ''}`} onClick={() => change({ object: String(asset.id) })} title={asset.name}><span>{iconFor(asset.type_name)}</span><span className="object-list-name">{asset.name}</span></button>)}</div>
            <div className="object-list-footer">{pagination.pages > 1 ? <><button disabled={pagination.page === 1} onClick={() => change({ page: String(pagination.page - 1) })}>‹</button><span>{pagination.page} / {pagination.pages}</span><button disabled={pagination.page === pagination.pages} onClick={() => change({ page: String(pagination.page + 1) })}>›</button></> : <span>{pagination.total} objetos</span>}</div>
          </div>
          <div className="object-detail-panel">{selectedObject ? <AssetDetail key={selectedObject} assetId={selectedObject} embedded onChanged={() => setReloadKey(k => k + 1)} /> : !loading && <div className="asset-empty">Selecciona un objeto</div>}</div>
        </div> : <>
        <div className="schema-toolbar">{selectedType && <span className="schema-toolbar-link" onClick={() => change({ view: '', object: '', page: '1' })}>◧ Vista dividida</span>}<span>☷ Acciones en masa</span><span>☰ Filtrar</span></div>
        <div className="asset-table-wrap">{loading ? <div className="asset-empty">Cargando activos…</div> : assets.length === 0 ? <div className="asset-empty">No se encontraron activos</div> : <table className="jira-table"><thead><tr><th>Icono</th><th>Clave</th><th>Nombre</th><th>Creado</th><th>Actualizado</th><th>Tipo</th></tr></thead><tbody>{assets.map((asset) => <tr key={asset.id}><td>{iconFor(asset.type_name)}</td><td><Link to={`/assets/${asset.id}`}>{asset.jira_key}</Link></td><td><Link to={`/assets/${asset.id}`}>{asset.name}</Link></td><td>{formatDate(asset.jira_created_at || asset.created_at)}</td><td>{formatDate(asset.jira_updated_at || asset.updated_at)}</td><td><span className="type-pill">{asset.type_name}</span></td></tr>)}</tbody></table>}</div>
        <div className="schema-pagination"><span>{assets.length ? `${(pagination.page - 1) * 50 + 1}-${Math.min(pagination.page * 50, pagination.total)} de ${pagination.total} objetos` : '0 objetos'}</span><div><button disabled={pagination.page === 1} onClick={() => change({ page: String(pagination.page - 1) })}>‹</button><strong>{pagination.page}</strong><button disabled={pagination.page === pagination.pages} onClick={() => change({ page: String(pagination.page + 1) })}>›</button></div></div>
        </>}
      </section>
    </div>
  </div>
}
