import React, { useState } from 'react'
import axios from 'axios'

const fullDate = (value) => value ? new Intl.DateTimeFormat('es-PE', { dateStyle: 'long', timeStyle: 'short' }).format(new Date(value)) : '—'
const dayLabel = (value) => value ? new Intl.DateTimeFormat('es-PE', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value)) : 'Sin fecha'
const initials = (name = '') => name.split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase() || '?'
// El backend guarda las fechas en UTC sin zona; se marca como UTC para mostrarlas en hora local.
const asUtc = (value) => value && !/[zZ]|[+-]\d\d:?\d\d$/.test(value) ? `${value}Z` : value

/**
 * Pestaña Actividad: caja para comentar + línea de tiempo que mezcla los comentarios
 * (guardados en la base de la plataforma; la sincronización con Jira no los toca)
 * y el historial de cambios importado de Jira, del más reciente al más antiguo.
 */
export default function ActivityFeed({ asset, onChange }) {
  const [draft, setDraft] = useState('')
  const [writing, setWriting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editing, setEditing] = useState(null) // { id, body }
  const [error, setError] = useState('')

  const run = async (action) => {
    setSaving(true); setError('')
    try { await action(); await onChange(); return true }
    catch (e) { setError(e.response?.data?.message || 'No se pudo guardar el comentario'); return false }
    finally { setSaving(false) }
  }
  const add = async () => { if (draft.trim() && await run(() => axios.post(`/api/assets/${asset.id}/comments`, { body: draft }))) { setDraft(''); setWriting(false) } }
  const saveEdit = async () => { if (editing.body.trim() && await run(() => axios.put(`/api/comments/${editing.id}`, { body: editing.body }))) setEditing(null) }
  const remove = (id) => { if (window.confirm('¿Eliminar este comentario?')) run(() => axios.delete(`/api/comments/${id}`)) }
  const onKey = (e, submit) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); submit() } }

  const entries = [
    ...(asset.comments || []).map(c => ({ kind: 'comment', key: `c${c.id}`, date: asUtc(c.created_at), data: c })),
    ...(asset.activities || []).map(a => ({ kind: 'history', key: `h${a.id}`, date: a.created_at, data: a })),
  ].sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0))

  let lastDay = null
  return <div className="detail-activity">
    <div className="comment-composer">
      {writing ? <>
        <textarea autoFocus rows={3} value={draft} placeholder="Escribe un comentario…" onChange={e => setDraft(e.target.value)} onKeyDown={e => onKey(e, add)} />
        <div className="comment-actions">
          <button className="comment-save" disabled={saving || !draft.trim()} onClick={add}>{saving ? 'Guardando…' : 'Guardar'}</button>
          <button className="comment-cancel" onClick={() => { setWriting(false); setDraft('') }}>Cancelar</button>
          <span className="comment-hint">Ctrl + Enter para guardar</span>
        </div>
      </> : <button className="comment-placeholder" onClick={() => setWriting(true)}>Añadir un comentario…</button>}
      {error && <p className="comment-error">{error}</p>}
    </div>
    {entries.length === 0 && <p className="activity-empty">No hay actividad registrada para este objeto todavía.</p>}
    {entries.map(entry => {
      const day = dayLabel(entry.date); const header = day !== lastDay; lastDay = day
      const item = entry.data
      return <React.Fragment key={entry.key}>
        {header && <div className="activity-day">{day}</div>}
        {entry.kind === 'comment' ? <div className="activity-entry activity-comment">
          <div className="activity-entry-head">
            <span className="comment-avatar">{initials(item.author_name)}</span><strong>{item.author_name}</strong>
            <span>comentó · {fullDate(entry.date)}{item.updated_at ? ' (editado)' : ''}</span>
            {editing?.id !== item.id && <span className="comment-tools"><button onClick={() => setEditing({ id: item.id, body: item.body })}>Editar</button><button onClick={() => remove(item.id)}>Eliminar</button></span>}
          </div>
          {editing?.id === item.id ? <div className="comment-composer">
            <textarea autoFocus rows={3} value={editing.body} onChange={e => setEditing({ ...editing, body: e.target.value })} onKeyDown={e => onKey(e, saveEdit)} />
            <div className="comment-actions"><button className="comment-save" disabled={saving || !editing.body.trim()} onClick={saveEdit}>Guardar</button><button className="comment-cancel" onClick={() => setEditing(null)}>Cancelar</button></div>
          </div> : <p className="comment-body">{item.body}</p>}
        </div> : <div className="activity-entry">
          <div className="activity-entry-head"><strong>{item.actor_name || 'Jira'}</strong><span>{fullDate(item.created_at)}</span></div>
          <p>{!item.affected_attribute ? 'Creó este objeto.' : <>Cambió <b>{item.affected_attribute}</b>{item.old_value ? <> de «{item.old_value}»</> : null} a «{item.new_value || '—'}».</>}</p>
        </div>}
      </React.Fragment>
    })}
  </div>
}
