import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import axios from 'axios'
import ReferenceField from '../components/ReferenceField'

const USER_FIELDS = ['DOC DE IDENTIDAD', 'APELLIDOS Y NOMBRES', 'Estado', 'FECHA DE INGRESO', 'CARGO', 'AREA DE TRABAJO', 'JEFE INMEDIATO', 'CARGO DEL JEFE INMEDIATO', 'CORREO PERSONAL', 'TELEFONO PERSONAL', 'CORREO DE LA EMPRESA', 'CONTRASEÑA DE CORREO', 'Código de recuperación MFA']
const EQUIPMENT_FIELDS = ['Estado del Equipo', 'IP', 'Modelo de equipo', 'Observaciones', 'Usuario Final', 'Fabricante', 'N° Serie', 'IMEI', 'Licencia Office 2013', 'Licencia Office 2016', 'Licencia Office 2019', 'Licencia M365 PBI 1', 'Licencia M365 PBI 2', 'Licencia M365 PBI 3', 'Anydesk']
// El campo "Activo de Contabilidad" (nombre real del atributo en Jira) solo se muestra, con esta
// etiqueta y su foto asociada, para los tipos de equipo que llevan código de contabilidad físico.
const ACCOUNTING_CODE_FIELD = 'Activo de Contabilidad'
const ACCOUNTING_CODE_LABEL = 'Código de activo de contabilidad'
const ACCOUNTING_IMAGE_FIELD = 'Img de código de contabilidad'
const ACCOUNTING_TYPES = ['Laptop', 'All In One', 'CPU', 'Monitor', 'Impresoras']
const fieldLabel = (field) => field === ACCOUNTING_CODE_FIELD ? ACCOUNTING_CODE_LABEL : field
const iconFor = (name = '') => /laptop|all in one/i.test(name) ? '💻' : /celular|móvil|tablet/i.test(name) ? '📱' : /software|office|windows/i.test(name) ? '💿' : /usuario/i.test(name) ? '👤' : '▣'
const display = (value) => Array.isArray(value) ? value.join(', ') : String(value || '')

export default function AssetDetail() {
  const { id } = useParams(); const [asset, setAsset] = useState(null); const [loading, setLoading] = useState(true); const [tab, setTab] = useState('details'); const [message, setMessage] = useState(''); const [touched, setTouched] = useState({})
  const load = () => axios.get(`/api/assets/${id}`).then(r => setAsset(r.data.data)).catch(console.error).finally(() => setLoading(false))
  useEffect(() => { setLoading(true); setTouched({}); load() }, [id])
  const markTouched = (field) => setTouched(current => current[field] ? current : { ...current, [field]: true })
  const save = async (payload) => { try { await axios.put(`/api/assets/${id}`, payload); await load(); setMessage('Guardado'); setTimeout(() => setMessage(''), 1800) } catch { setMessage('No se pudo guardar') } }
  if (loading) return <div className="detail-loading">Cargando objeto…</div>
  if (!asset) return <div className="detail-loading">No se encontró este objeto.</div>
  const isUser = asset.type_name === 'Usuario'; const attributes = asset.attributes || {}
  const baseFields = isUser ? USER_FIELDS : EQUIPMENT_FIELDS
  const typeFields = !isUser && ACCOUNTING_TYPES.includes(asset.type_name) ? [...baseFields, ACCOUNTING_CODE_FIELD, ACCOUNTING_IMAGE_FIELD] : baseFields
  const fields = [...new Set([...typeFields, ...Object.keys(attributes)])]
  const referenceFor = (field) => asset.relations?.find(r => r.relation_type === field)
  const date = (value) => value ? new Intl.DateTimeFormat('es-PE', { dateStyle: 'long', timeStyle: 'short' }).format(new Date(value)) : '—'
  const check = () => <span className="field-check" title="Completo">✓</span>
  const valueControl = (field) => {
    if (field === 'Usuario Final' || field === 'Fabricante') {
      const ref = referenceFor(field)
      return <div className="field-with-check" onFocusCapture={() => markTouched(field)} onClickCapture={() => markTouched(field)}><ReferenceField kind={field === 'Usuario Final' ? 'users' : 'brands'} value={ref ? { id: ref.target_asset_id, name: ref.target_asset_name } : null} onChange={option => save({ references: { [field]: option?.id || null } })} />{ref && touched[field] && check()}</div>
    }
    if (field === ACCOUNTING_IMAGE_FIELD) {
      const value = display(attributes[field])
      const onFile = (e) => {
        const file = e.target.files?.[0]
        if (!file) return
        const reader = new FileReader()
        reader.onload = () => save({ attributes: { [field]: reader.result } })
        reader.readAsDataURL(file)
        e.target.value = ''
      }
      const copyImage = async () => {
        try {
          const blob = await (await fetch(value)).blob()
          await navigator.clipboard.write([new window.ClipboardItem({ [blob.type]: blob })])
          setMessage('Imagen copiada'); setTimeout(() => setMessage(''), 1800)
        } catch {
          setMessage('No se pudo copiar la imagen'); setTimeout(() => setMessage(''), 1800)
        }
      }
      return <div className="attachment-field" onFocusCapture={() => markTouched(field)} onClickCapture={() => markTouched(field)}>
        {value && <img src={value} alt={ACCOUNTING_IMAGE_FIELD} className="attachment-preview" title="Clic para copiar la imagen" onClick={copyImage} />}
        <input type="file" accept="image/*" onChange={onFile} />
        {value && <button type="button" className="attachment-remove" onClick={() => save({ attributes: { [field]: '' } })}>Quitar foto</button>}
        {value && touched[field] && check()}
      </div>
    }
    const choices = field === 'Estado del Equipo' ? ['Inactivo', 'Retirado', 'En uso', 'Disponible'] : field === 'Estado' ? ['Activo', 'Inactivo'] : null
    if (choices) { const selected = display(attributes[field]); const tone = /activo|uso/i.test(selected) && !/inactivo/i.test(selected) ? 'status-positive' : /inactivo|retirado/i.test(selected) ? 'status-negative' : 'status-neutral'; return <div className="field-with-check" onFocusCapture={() => markTouched(field)} onClickCapture={() => markTouched(field)}><select className={tone} value={selected} onChange={e => save({ attributes: { [field]: e.target.value } })}>{!attributes[field] && <option value="">Seleccionar…</option>}{choices.map(item => <option key={item}>{item}</option>)}</select>{selected && touched[field] && check()}</div> }
    const value = display(attributes[field])
    return <div className="field-with-check" onFocusCapture={() => markTouched(field)} onClickCapture={() => markTouched(field)}><input value={value} placeholder="Añadir información" onChange={e => setAsset(current => ({ ...current, attributes: { ...current.attributes, [field]: e.target.value } }))} onBlur={e => save({ attributes: { [field]: e.target.value } })} />{value && touched[field] && check()}</div>
  }
  return <div className="detail-screen">
    <div className="detail-breadcrumb"><Link to="/assets">Activos de TI</Link><span>/</span><Link to={`/assets?type=${asset.type_id}`}>{asset.type_name}</Link><span>/</span>{asset.jira_key}</div>
    <div className="detail-heading"><div className="detail-heading-name"><span>{iconFor(asset.type_name)}</span><input className="asset-name-input" value={asset.name} onChange={e => setAsset({ ...asset, name: e.target.value })} onBlur={e => save({ name: e.target.value })} />{asset.name && check()}</div><div className="detail-actions"><span className="save-message">{message}</span><button title="Copiar enlace">↗</button><button title="Más acciones">•••</button></div></div>
    <div className="detail-grid"><section className="detail-main"><div className="detail-tabs"><button className={tab === 'details' ? 'active' : ''} onClick={() => setTab('details')}>Detalles</button><button className={tab === 'activity' ? 'active' : ''} onClick={() => setTab('activity')}>Actividad</button></div>
      {tab === 'details' ? <div className="detail-properties">{fields.map(field => <div className="detail-property editable-property" key={field}><dt>{fieldLabel(field)}</dt><dd>{valueControl(field)}</dd></div>)}</div> : <div className="detail-activity">
        {asset.activities?.length ? asset.activities.map(a => <div className="activity-entry" key={a.id}>
          <div className="activity-entry-head"><strong>{a.actor_name || 'Jira'}</strong><span>{date(a.created_at)}</span></div>
          <p>{!a.affected_attribute ? 'Creó este objeto.' : <>Cambió <b>{a.affected_attribute}</b>{a.old_value ? <> de «{a.old_value}»</> : null} a «{a.new_value || '—'}».</>}</p>
        </div>) : <p className="activity-empty">No hay actividad registrada para este objeto. Sincroniza con Jira para importar el historial.</p>}
      </div>}
    </section><aside className="detail-side"><section className="linked-card"><header><strong>Objetos vinculados</strong><span>⌘ Gráfico de objetos</span></header><div className="linked-body"><b>Referencias salientes</b>{asset.relations?.length ? asset.relations.map(rel => <div className="linked-row" key={rel.id}><span>— {rel.relation_type} →</span><Link to={`/assets/${rel.target_asset_id}`}>{iconFor(rel.target_asset_type)} {rel.target_asset_name}</Link></div>) : <p>No hay objetos vinculados.</p>}<b className="incoming-title">Referencias entrantes</b>{asset.incoming_relations?.length ? asset.incoming_relations.map(rel => <div className="linked-row" key={rel.id}><span>← {rel.relation_type}</span><Link to={`/assets/${rel.source_asset_id}`}>{iconFor(rel.source_asset_type)} {rel.source_asset_name}</Link></div>) : <p>No hay referencias entrantes.</p>}</div></section><section className="detail-side-section"><h3>Actividades vinculadas</h3><div className="empty-outline">No se encontraron actividades</div></section><section className="detail-side-section"><h3>Adjuntos <span>＋</span></h3><div className="empty-outline">☁ Añadir adjunto</div></section><div className="detail-dates">Fecha de creación: {date(asset.jira_created_at || asset.created_at)}<br />Fecha de modificación: {date(asset.jira_updated_at || asset.updated_at)}</div></aside></div>
  </div>
}
