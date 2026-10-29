import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

export default function AssetHierarchy() {
  const [hierarchy, setHierarchy] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedNodes, setExpandedNodes] = useState(new Set())
  const [totalNodes, setTotalNodes] = useState(0)

  useEffect(() => {
    fetchHierarchy()
  }, [])

  const fetchHierarchy = async () => {
    setLoading(true)
    try {
      const res = await axios.get('/api/assets/tree/hierarchy')
      setHierarchy(res.data.data)
      setTotalNodes(countNodes(res.data.data))
    } catch (err) {
      console.error('Error fetching hierarchy:', err)
    } finally {
      setLoading(false)
    }
  }

  const countNodes = (items) => {
    return items.reduce((acc, item) => acc + 1 + (item.children ? countNodes(item.children) : 0), 0)
  }

  const getAllIds = (items) => {
    return items.reduce((acc, item) => {
      acc.push(item.id)
      if (item.children?.length) acc.push(...getAllIds(item.children))
      return acc
    }, [])
  }

  const toggleNode = (id) => {
    setExpandedNodes(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const expandAll = () => setExpandedNodes(new Set(getAllIds(hierarchy)))
  const collapseAll = () => setExpandedNodes(new Set())

  const renderTree = (items, level = 0) => (
    <ul>
      {items.map(item => {
        const hasChildren = item.children?.length > 0
        const isExpanded = expandedNodes.has(item.id)

        return (
          <li key={item.id}>
            <div className="hier-row" style={{ paddingLeft: `${level * 18}px` }}>
              <button onClick={() => hasChildren && toggleNode(item.id)} className={`hier-toggle ${hasChildren ? '' : 'leaf'}`}>
                {hasChildren ? (isExpanded ? '▼' : '▶') : '•'}
              </button>
              <div className="hier-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m0 0l8 4m-8-4v10l8 4m0-10l8-4m-8 4v10l8-4" /></svg>
              </div>
              <Link to={`/assets/${item.id}`} className="hier-name">{item.name}</Link>
              <span className="hier-type">{item.type_name}</span>
              {hasChildren && <span className="hier-count">{item.children.length}</span>}
            </div>
            {isExpanded && hasChildren && renderTree(item.children, level + 1)}
          </li>
        )
      })}
    </ul>
  )

  return (
    <div className="hier fade-in">
      <div className="hier-head">
        <div>
          <h1>Vista Jerárquica</h1>
          <p>{totalNodes > 0 ? `${totalNodes.toLocaleString()} activos en el árbol` : 'Estructura de activos'}</p>
        </div>
        <button onClick={fetchHierarchy} className="btn-outline">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          Recargar
        </button>
      </div>

      <div className="hier-card">
        {loading ? (
          <div className="hier-empty">Cargando jerarquía…</div>
        ) : hierarchy.length === 0 ? (
          <div className="hier-empty">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>
            No hay activos para mostrar. Sincroniza primero desde el Dashboard.
          </div>
        ) : (
          <>
            <div className="hier-toolbar">
              <button onClick={expandAll} className="hier-pill hier-pill-teal">Expandir todo</button>
              <button onClick={collapseAll} className="hier-pill hier-pill-muted">Contraer todo</button>
              <span>{expandedNodes.size} nodos expandidos</span>
            </div>

            <div className="hier-tree">{renderTree(hierarchy)}</div>

            <div className="hier-foot">Haz clic en ▶ para expandir · Haz clic en el nombre para ver detalles · El número indica cantidad de hijos directos</div>
          </>
        )}
      </div>
    </div>
  )
}
