import React, { useEffect, useRef, useState } from 'react'
import axios from 'axios'

const iconFor = (name = '') => /laptop|all in one/i.test(name) ? '💻' : /celular|móvil|tablet/i.test(name) ? '📱' : /software|office|windows|licencia|ms 365/i.test(name) ? '💿' : /impresora/i.test(name) ? '🖨️' : /usuario/i.test(name) ? '👤' : /marca|fabricante/i.test(name) ? '◉' : '▣'

// Resalta en negrita las partes del texto que coinciden con alguna palabra buscada.
function Highlight({ text = '', query }) {
  const tokens = query.trim().split(/\s+/).filter(Boolean).map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  if (!tokens.length) return text
  const parts = String(text).split(new RegExp(`(${tokens.join('|')})`, 'gi'))
  return parts.map((part, i) => i % 2 ? <mark key={i}>{part}</mark> : part)
}

/**
 * Buscador con autocompletado desde la primera letra (nombre, clave, DNI, serie, IMEI...).
 * - typeId: limita las sugerencias a un tipo de objeto (buscador del esquema).
 * - onSelect(item): al elegir una sugerencia.
 * - onSubmit(query): Enter sin sugerencia marcada, o "Ver todos los resultados".
 * - onClear(): al pulsar la × para borrar el texto.
 */
export default function SearchBox({ placeholder, typeId, initialValue = '', onSelect, onSubmit, onClear, className = '' }) {
  const [query, setQuery] = useState(initialValue)
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [loading, setLoading] = useState(false)
  const requestId = useRef(0)

  useEffect(() => { setQuery(initialValue) }, [initialValue])

  useEffect(() => {
    const q = query.trim()
    if (!q || !open) { setItems([]); setTotal(0); return }
    const id = ++requestId.current
    setLoading(true)
    const timeout = setTimeout(() => {
      axios.get('/api/search/suggestions', { params: { q, type_id: typeId || undefined, limit: 8 } })
        .then(r => { if (id === requestId.current) { setItems(r.data.data); setTotal(r.data.total ?? r.data.data.length); setActive(-1) } })
        .catch(() => { if (id === requestId.current) setItems([]) })
        .finally(() => { if (id === requestId.current) setLoading(false) })
    }, 150)
    return () => clearTimeout(timeout)
  }, [query, typeId, open])

  const choose = (item) => { setOpen(false); setQuery(''); onSelect?.(item) }
  const submit = () => { setOpen(false); onSubmit?.(query.trim()) }
  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); setActive(a => Math.min(a + 1, items.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(a => Math.max(a - 1, -1)) }
    else if (e.key === 'Enter') { e.preventDefault(); active >= 0 && items[active] ? choose(items[active]) : submit() }
    else if (e.key === 'Escape') { setOpen(false) }
  }
  const clear = () => { setQuery(''); setItems([]); onClear?.() }
  const showPanel = open && query.trim()

  return <div className={`search-box ${className}`}>
    <span className="search-box-icon" aria-hidden="true">⌕</span>
    <input value={query} placeholder={placeholder} onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}
      onChange={e => { setQuery(e.target.value); setOpen(true) }} onKeyDown={onKeyDown} autoComplete="off" />
    {query && <button type="button" className="search-box-clear" title="Limpiar" onMouseDown={e => e.preventDefault()} onClick={clear}>×</button>}
    {showPanel && <div className="search-suggestions" onMouseDown={e => e.preventDefault()}>
      <div className="search-suggestions-title">Objetos</div>
      {items.map((item, i) => <button type="button" key={item.id} className={i === active ? 'active' : ''} onMouseEnter={() => setActive(i)} onClick={() => choose(item)}>
        <span className="search-suggestion-icon">{iconFor(item.type_name)}</span>
        <span className="search-suggestion-key"><Highlight text={item.jira_key} query={query} /></span>
        <span className="search-suggestion-text">
          <strong><Highlight text={item.name} query={query} /></strong>
          <small>{item.type_name}{item.matched_field && <> · {item.matched_field.name ? `${item.matched_field.name}: ` : ''}<Highlight text={item.matched_field.value} query={query} /></>}</small>
        </span>
      </button>)}
      {!items.length && <div className="search-suggestions-empty">{loading ? 'Buscando…' : 'Sin coincidencias'}</div>}
      {total > items.length && <button type="button" className="search-suggestions-more" onClick={submit}>Ver todos los resultados ({total})</button>}
    </div>}
  </div>
}
