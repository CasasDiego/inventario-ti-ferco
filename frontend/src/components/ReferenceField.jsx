import React, { useEffect, useRef, useState } from 'react'
import axios from 'axios'

const iconFor = (field) => field === 'Usuario Final' ? '👤' : field === 'Fabricante' ? '◉' : '💿'
const placeholderFor = (field) => field === 'Usuario Final' ? 'Seleccionar usuario…' : field === 'Fabricante' ? 'Seleccionar fabricante…' : 'Seleccionar licencia…'

/**
 * Desplegable de un campo de referencia (estilo Jira): al hacer clic muestra todas las opciones
 * del tipo correspondiente; escribiendo se filtran. Teclado: ↑ ↓ Enter Esc.
 */
export default function ReferenceField({ field, value, onChange }) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [options, setOptions] = useState([])
  const [loading, setLoading] = useState(false)
  const [active, setActive] = useState(-1)
  const listRef = useRef(null)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    const t = setTimeout(() => axios.get('/api/assets/options', { params: { field, q: query } })
      .then(r => { setOptions(r.data.data); setActive(-1) })
      .catch(console.error)
      .finally(() => setLoading(false)), query ? 160 : 0)
    return () => clearTimeout(t)
  }, [open, query, field])

  useEffect(() => { listRef.current?.querySelector('.active')?.scrollIntoView({ block: 'nearest' }) }, [active])

  const choose = (option) => { setOpen(false); setQuery(''); if (option.id !== value?.id) onChange(option) }
  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); setActive(a => Math.min(a + 1, options.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(a => Math.max(a - 1, 0)) }
    else if (e.key === 'Enter' && open && options[active]) { e.preventDefault(); choose(options[active]) }
    else if (e.key === 'Escape') { setOpen(false); e.target.blur() }
  }

  return <div className={`reference-control ${open ? 'reference-open' : ''}`}>
    <input value={open ? query : (value?.name || '')} placeholder={open ? 'Escribe para filtrar…' : placeholderFor(field)}
      onFocus={() => { setOpen(true); setQuery('') }} onBlur={() => setOpen(false)}
      onChange={e => { setQuery(e.target.value); setOpen(true) }} onKeyDown={onKeyDown} />
    {value && !open && <button type="button" className="reference-clear" title="Quitar" onMouseDown={e => e.preventDefault()} onClick={() => onChange(null)}>×</button>}
    <span className="reference-chevron" aria-hidden="true">⌄</span>
    {open && <div className="reference-options" ref={listRef} onMouseDown={e => e.preventDefault()}>
      {options.map((option, i) => <button type="button" key={option.id} className={`${i === active ? 'active' : ''} ${option.id === value?.id ? 'selected' : ''}`} onMouseEnter={() => setActive(i)} onClick={() => choose(option)}>
        <span className="reference-option-icon">{iconFor(field)}</span>
        <span className="reference-option-text"><strong>{option.name}</strong>{(option.detail || option.name !== option.jira_key) && <small>{option.name !== option.jira_key ? option.jira_key : ''}{option.detail ? `${option.name !== option.jira_key ? ' · ' : ''}${option.detail}` : ''}</small>}</span>
        {option.id === value?.id && <span className="reference-option-check">✓</span>}
      </button>)}
      {!options.length && <span className="reference-empty">{loading ? 'Cargando…' : 'Sin resultados'}</span>}
    </div>}
  </div>
}
