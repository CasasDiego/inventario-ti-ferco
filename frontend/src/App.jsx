import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import axios from 'axios'
import Navbar from './components/Navbar'
import AssetsList from './pages/AssetsList'
import AssetDetail from './pages/AssetDetail'
import Dashboard from './pages/Dashboard'
import AssetHierarchy from './pages/AssetHierarchy'
import Login from './pages/Login'

function App() {
  const [stats, setStats] = useState({ total_assets: 0, total_types: 0, total_relations: 0 })
  const [user, setUser] = useState(null)
  const [checkingSession, setCheckingSession] = useState(true)
  const fetchStats = async () => { try { setStats((await axios.get('/api/info')).data.database) } catch (error) { console.error(error) } }
  useEffect(() => { axios.get('/api/auth/me').then(r => { setUser(r.data.data); fetchStats() }).catch(() => {}).finally(() => setCheckingSession(false)) }, [])
  const logout = async () => { await axios.post('/api/auth/logout'); setUser(null) }
  if (checkingSession) return <div className="detail-loading">Cargando plataforma…</div>
  if (!user) return <Login onLogin={(loggedUser) => { setUser(loggedUser); fetchStats() }} />
  return <Router><div className="app-shell"><Navbar stats={stats} user={user} onLogout={logout} onAssetCreated={fetchStats} /><main className="app-main"><Routes>
    <Route path="/" element={<Dashboard stats={stats} onSync={fetchStats} />} />
    <Route path="/assets" element={<AssetsList />} />
    <Route path="/assets/:id" element={<AssetDetail />} />
    <Route path="/hierarchy" element={<AssetHierarchy />} />
  </Routes></main></div></Router>
}
export default App
