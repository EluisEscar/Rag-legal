import { useState } from 'react'
import { supabase } from './supabaseClient'
import './Login.css'

export default function Login({ onLogin }) {
  const [email,     setEmail]     = useState('')
  const [password,  setPassword]  = useState('')
  const [cargando,  setCargando]  = useState(false)
  const [error,     setError]     = useState('')
  const [modo,      setModo]      = useState('login') // 'login' | 'registro'

  const manejarSubmit = async () => {
    if (!email || !password) {
      setError('Completa todos los campos')
      return
    }
    setCargando(true)
    setError('')

    try {
      let resultado

      if (modo === 'login') {
        resultado = await supabase.auth.signInWithPassword({
          email,
          password
        })
      } else {
        resultado = await supabase.auth.signUp({
          email,
          password
        })
      }

      if (resultado.error) {
        setError(resultado.error.message)
      } else {
        onLogin(resultado.data.user)
      }
    } catch (e) {
      setError('Error de conexión')
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">

        <div className="login-logo">⚖️</div>
        <h1 className="login-title">LexPerú</h1>
        <p className="login-subtitle">Asistente Legal Especializado</p>

        <div className="login-tabs">
          <button
            className={`login-tab ${modo === 'login' ? 'active' : ''}`}
            onClick={() => setModo('login')}
          >
            Iniciar sesión
          </button>
          <button
            className={`login-tab ${modo === 'registro' ? 'active' : ''}`}
            onClick={() => setModo('registro')}
          >
            Registrarse
          </button>
        </div>

        <div className="login-form">
          <div className="login-field">
            <label>Correo electrónico</label>
            <input
              type="email"
              placeholder="abogado@estudio.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && manejarSubmit()}
            />
          </div>

          <div className="login-field">
            <label>Contraseña</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && manejarSubmit()}
            />
          </div>

          {error && <p className="login-error">⚠ {error}</p>}

          <button
            className="login-btn"
            onClick={manejarSubmit}
            disabled={cargando}
          >
            {cargando
              ? 'Cargando...'
              : modo === 'login' ? 'Entrar' : 'Crear cuenta'
            }
          </button>
        </div>

        <p className="login-footer">
          Plataforma segura para consultas legales peruanas
        </p>

      </div>
    </div>
  )
}