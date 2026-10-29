import React, { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import ReferenceField from './ReferenceField'

// Campos por tipo de objeto, replicando el formulario de Jira Assets.
// Se irán añadiendo más tipos aquí; los tipos sin entrada usan DEFAULT_FIELDS.
const TYPE_FIELDS = {
  'All In One': [
    { name: 'Estado del Equipo', kind: 'select', options: ['Inactivo', 'Retirado', 'En uso', 'Disponible'], help: 'Estado del activo (por ejemplo, disponible, en uso, etc.)' },
    { name: 'IP', kind: 'text' },
    { name: 'Modelo de equipo', kind: 'text', required: true, isName: true },
    { name: 'Observaciones', kind: 'text' },
    { name: 'Usuario Final', kind: 'reference', refKind: 'users' },
    { name: 'Fabricante', kind: 'reference', refKind: 'brands', help: 'Fabricante' },
    { name: 'N° Serie', kind: 'text', help: 'Serie del producto' },
    { name: 'Activo de Contabilidad', label: 'Código de activo de contabilidad', kind: 'text', help: 'Código de contabilidad del equipo' },
    { name: 'Img de código de contabilidad', kind: 'image', help: 'Foto del código/QR de contabilidad' },
    { name: 'Licencia Office 2013', kind: 'text', help: 'Colocar el código de licencia que le figure' },
    { name: 'Licencia Office 2016', kind: 'text', help: 'Colocar el código de licencia que le figure' },
    { name: 'Licencia Office 2019', kind: 'text', help: 'Colocar el código de licencia que le figure' },
    { name: 'Anydesk', kind: 'text', help: 'Colocar el anydesk del dispositivo' },
    { name: 'Licencia MS 365 PB1', kind: 'text', help: 'Colocar el código de licencia que le figure' },
    { name: 'Licencia MS 365 PB2', kind: 'text', help: 'Colocar el código de licencia que le figure' },
    { name: 'Licencia MS 365 PB3', kind: 'text', help: 'Colocar el código de licencia que le figure' }
  ],
  'Laptop': [
    { name: 'Estado del Equipo', kind: 'select', options: ['Inactivo', 'Retirado', 'En uso', 'Disponible'], help: 'Estado del activo (por ejemplo, disponible, en uso, etc.)' },
    { name: 'IP', kind: 'text' },
    { name: 'Modelo de equipo', kind: 'text', required: true, isName: true },
    { name: 'Observaciones', kind: 'text' },
    { name: 'Usuario Final', kind: 'reference', refKind: 'users' },
    { name: 'Fabricante', kind: 'reference', refKind: 'brands', help: 'Fabricante' },
    { name: 'Anydesk', kind: 'text', help: 'Colocar el anydesk para la conexion remota' },
    { name: 'N° Serie', kind: 'text', help: 'Serie del producto' },
    { name: 'Activo de Contabilidad', label: 'Código de activo de contabilidad', kind: 'text', help: 'Código de contabilidad del equipo' },
    { name: 'Img de código de contabilidad', kind: 'image', help: 'Foto del código/QR de contabilidad' },
    { name: 'Licencia Office 2013', kind: 'text', help: 'Colocar el código de licencia que pertenece' },
    { name: 'Licencia Office 2016', kind: 'text', help: 'Colocar el código de licencia que pertenece' },
    { name: 'Licencia Office 2019', kind: 'text', help: 'Colocar el código de licencia que pertenece' },
    { name: 'Licencia M365 PBI 1', kind: 'text', help: 'Colocar cual de las 5 se usará' },
    { name: 'Licencia M365 PBI 2', kind: 'text', help: 'Colocar cual de las 5 se usará' },
    { name: 'Licencia M365 PBI 3', kind: 'text', help: 'Colocar cual de las 5 se usará' }
  ],
  'Celular': [
    { name: 'Estado del Equipo', kind: 'select', options: ['Inactivo', 'Retirado', 'En uso', 'Disponible'], help: 'Estado del activo (por ejemplo, disponible, en uso, etc.)' },
    { name: 'IP', kind: 'text' },
    { name: 'Modelo de equipo', kind: 'text', required: true, isName: true },
    { name: 'Observaciones', kind: 'text' },
    { name: 'Usuario Final', kind: 'reference', refKind: 'users' },
    { name: 'Fabricante', kind: 'reference', refKind: 'brands' },
    { name: 'N° Serie', kind: 'text', help: 'Serie del producto' },
    { name: 'IMEI', kind: 'text' },
    { name: 'Número de teléfono', kind: 'text' }
  ],
  'CPU': [
    { name: 'Nombre', kind: 'text', required: true, isName: true },
    { name: 'Activo de Contabilidad', label: 'Código de activo de contabilidad', kind: 'text', help: 'Código de contabilidad del equipo' },
    { name: 'Img de código de contabilidad', kind: 'image', help: 'Foto del código/QR de contabilidad' }
  ],
  'Monitor': [
    { name: 'Nombre', kind: 'text', required: true, isName: true },
    { name: 'Activo de Contabilidad', label: 'Código de activo de contabilidad', kind: 'text', help: 'Código de contabilidad del equipo' },
    { name: 'Img de código de contabilidad', kind: 'image', help: 'Foto del código/QR de contabilidad' }
  ],
  'Impresoras': [
    { name: 'Nombre', kind: 'text', required: true, isName: true },
    { name: 'Activo de Contabilidad', label: 'Código de activo de contabilidad', kind: 'text', help: 'Código de contabilidad del equipo' },
    { name: 'Img de código de contabilidad', kind: 'image', help: 'Foto del código/QR de contabilidad' }
  ]
}
const DEFAULT_FIELDS = [{ name: 'Nombre', kind: 'text', required: true, isName: true }]

export default function CreateAssetModal({ open, onClose, onCreated, initialTypeId }) {
  const [types, setTypes] = useState([])
  const [typeId, setTypeId] = useState('')
  const [values, setValues] = useState({})
  const [createAnother, setCreateAnother] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { if (open) axios.get('/api/asset-types').then(r => setTypes(r.data.data)).catch(console.error) }, [open])
  useEffect(() => { if (open) { setTypeId(initialTypeId || ''); setValues({}); setError(''); setCreateAnother(false) } }, [open, initialTypeId])

  const selectedType = useMemo(() => types.find(t => String(t.id) === typeId), [types, typeId])
  const fields = TYPE_FIELDS[selectedType?.name] || DEFAULT_FIELDS

  const setValue = (name, value) => setValues(current => ({ ...current, [name]: value }))

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    const nameField = fields.find(f => f.isName)
    const name = (nameField ? values[nameField.name] : '') || ''
    if (!typeId || !name.trim()) { setError('Completa los campos obligatorios.'); return }

    const attributes = Object.fromEntries(fields.filter(f => f.kind !== 'reference').map(f => [f.name, values[f.name] || '']))
    const references = Object.fromEntries(fields.filter(f => f.kind === 'reference' && values[f.name]).map(f => [f.name, values[f.name].id]))

    setSubmitting(true)
    try {
      const response = await axios.post('/api/assets', { name, type_id: Number(typeId), attributes, references })
      if (createAnother) { setValues({}) } else { onCreated?.(response.data.data); onClose() }
    } catch (err) {
      setError(err.response?.data?.message || 'No se pudo crear el objeto.')
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) return null

  return (
    <div className="modal-overlay" onMouseDown={onClose}>
      <div className="modal-card" onMouseDown={(e) => e.stopPropagation()}>
        <div className="modal-header"><h2>Crear objeto</h2><button type="button" onClick={onClose} aria-label="Cerrar">×</button></div>
        <form onSubmit={submit}>
          <div className="modal-body">
            <p className="modal-required-hint"><span>*</span> indica un campo obligatorio.</p>
            <label className="modal-field"><span>Esquema *</span><select value="1" disabled><option value="1">Activos de Ti</option></select></label>
            <label className="modal-field">
              <span>Tipo de objetos *</span>
              <select value={typeId} onChange={(e) => { setTypeId(e.target.value); setValues({}) }} required>
                <option value="">Ninguno</option>
                {types.map((type) => <option key={type.id} value={type.id}>{type.name}</option>)}
              </select>
            </label>
            {selectedType && <>
              <div className="modal-divider" />
              {fields.map((field) => {
                const filled = field.kind === 'reference' ? !!values[field.name] : !!String(values[field.name] || '').trim()
                const check = <span className="field-check" title="Completo">✓</span>
                return (
                  <label className="modal-field" key={field.name}>
                    <span>{field.label || field.name}{field.required ? ' *' : ''}</span>
                    {field.kind === 'image' ? (
                      <div className="attachment-field">
                        {values[field.name] && <img src={values[field.name]} alt={field.name} className="attachment-preview" title="Clic para copiar la imagen" onClick={async () => {
                          try {
                            const blob = await (await fetch(values[field.name])).blob()
                            await navigator.clipboard.write([new window.ClipboardItem({ [blob.type]: blob })])
                          } catch { /* clipboard no disponible */ }
                        }} />}
                        <input type="file" accept="image/*" onChange={(e) => {
                          const file = e.target.files?.[0]
                          if (!file) return
                          const reader = new FileReader()
                          reader.onload = () => setValue(field.name, reader.result)
                          reader.readAsDataURL(file)
                        }} />
                        {filled && check}
                      </div>
                    ) : (
                      <div className="field-with-check">
                        {field.kind === 'select' ? (
                          <select value={values[field.name] || ''} onChange={(e) => setValue(field.name, e.target.value)}>
                            <option value="">Seleccionar…</option>
                            {field.options.map((option) => <option key={option}>{option}</option>)}
                          </select>
                        ) : field.kind === 'reference' ? (
                          <ReferenceField kind={field.refKind} value={values[field.name]} onChange={(option) => setValue(field.name, option)} />
                        ) : (
                          <input value={values[field.name] || ''} required={field.required} onChange={(e) => setValue(field.name, e.target.value)} />
                        )}
                        {filled && check}
                      </div>
                    )}
                    {field.help && <small>{field.help}</small>}
                  </label>
                )
              })}
            </>}
            {error && <p className="modal-error">{error}</p>}
          </div>
          <div className="modal-footer">
            <label className="modal-checkbox"><input type="checkbox" checked={createAnother} onChange={(e) => setCreateAnother(e.target.checked)} /> Crear otro</label>
            <div>
              <button type="button" className="modal-btn-secondary" onClick={onClose}>Cancelar</button>
              <button type="submit" className="modal-btn-primary" disabled={submitting || !typeId}>Crear</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
