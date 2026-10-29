import React, { useState } from 'react'
import axios from 'axios'
import logo from '../../img/Ferco-logo.png'

export default function Login({ onLogin }) {
  const [email, setEmail] = useState(localStorage.getItem('ferco_email') || 'dcasas@ferco-medical.com')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const submit = async (event) => {
    event.preventDefault(); setLoading(true); setError('')
    try { const response = await axios.post('/api/auth/login', { email, password }); localStorage.setItem('ferco_email', email); onLogin(response.data.data) }
    catch (err) { setError(err.response?.data?.message || 'No se pudo iniciar sesión') }
    finally { setLoading(false) }
  }
  return <main className="login-page"><section className="login-card"><img src={logo} alt="Ferco Medical" /><p className="login-kicker">PLATAFORMA DE ACTIVOS</p><h1>Bienvenido</h1><p className="login-copy">Ingresa para administrar los activos de Ferco Medical.</p><form onSubmit={submit}><label>Correo corporativo<input type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" required /></label><label>Contraseña<input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required /></label>{error && <p className="login-error">{error}</p>}<button disabled={loading}>{loading ? 'Ingresando…' : 'Iniciar sesión'}</button></form></section><div className="login-orb login-orb-one" /><div className="login-orb login-orb-two" /></main>
}
