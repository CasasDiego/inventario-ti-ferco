import React, { useEffect, useState } from 'react'
import axios from 'axios'

export default function ReferenceField({ kind, value, onChange }) {
  const [open, setOpen] = useState(false); const [query, setQuery] = useState(''); const [options, setOptions] = useState([])
  useEffect(() => { if (!open) return; const t = setTimeout(() => axios.get('/api/assets/options', { params: { kind, q: query } }).then(r => setOptions(r.data.data)).catch(console.error), 160); return () => clearTimeout(t) }, [open, query, kind])
  return <div className="reference-control"><input value={open ? query : (value?.name || '')} onFocus={() => { setOpen(true); setQuery(value?.name || '') }} onChange={e => { setQuery(e.target.value); setOpen(true) }} onBlur={() => setOpen(false)} placeholder={kind === 'users' ? 'Buscar usuario…' : 'Buscar fabricante…'} />{value && <button type="button" onClick={() => onChange(null)}>×</button>}{open && <div className="reference-options">{options.length ? options.map(option => <button type="button" key={option.id} onMouseDown={() => { onChange(option); setOpen(false); setQuery('') }}>{kind === 'users' ? '👤' : '◉'} {option.name}</button>) : <span>Sin resultados</span>}</div>}</div>
}
