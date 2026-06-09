import { useEffect, useRef, useState } from 'react'
import { supabase } from './supabaseClient'
import Login from './Login'
import './App.css'

const API = 'http://localhost:8000'

const CONVS_INICIALES = [
  { id: 1, titulo: 'Derechos fundamentales', fecha: 'Hoy' },
  { id: 2, titulo: 'Análisis de contrato laboral', fecha: 'Ayer' },
  { id: 3, titulo: 'Hábeas corpus', fecha: '05 jun' },
]

function Icon({ name, size = 20 }) {
  const paths = {
    scale: (
      <>
        <path d="M12 3v18M7 21h10M5 6h14M7 6l-4 7h8L7 6ZM17 6l-4 7h8l-4-7Z" />
        <path d="M3 13c.7 1.3 2 2 4 2s3.3-.7 4-2M13 13c.7 1.3 2 2 4 2s3.3-.7 4-2" />
      </>
    ),
    chat:   <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8Z" />,
    plus:   <path d="M12 5v14M5 12h14" />,
    moon:   <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z" />,
    sun: (
      <>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41" />
      </>
    ),
    dots: (
      <>
        <circle cx="5"  cy="12" r="1" fill="currentColor" stroke="none" />
        <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
        <circle cx="19" cy="12" r="1" fill="currentColor" stroke="none" />
      </>
    ),
    edit: (
      <>
        <path d="M12 20h9" />
        <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L8 18l-4 1 1-4Z" />
      </>
    ),
    trash: <path d="M3 6h18M8 6V4h8v2M19 6l-1 15H6L5 6M10 11v6M14 11v6" />,
    file: (
      <>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
        <path d="M14 2v6h6M8 13h8M8 17h5" />
      </>
    ),
    send: (
      <>
        <path d="m22 2-7 20-4-9-9-4Z" />
        <path d="M22 2 11 13" />
      </>
    ),
    menu:   <path d="M4 6h16M4 12h16M4 18h16" />,
    close:  <path d="m6 6 12 12M18 6 6 18" />,
    shield: (
      <>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
    logout: <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />,
  }

  return (
    <svg
      aria-hidden="true"
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  )
}

export default function App() {
  // ── Auth ──
  const [usuario,      setUsuario]      = useState(null)
  const [cargandoAuth, setCargandoAuth] = useState(true)

  // ── Chat ──
  const [mensajes,    setMensajes]    = useState([{
    rol:   'bot',
    texto: 'Hola, soy tu asistente legal especializado en derecho peruano. Puedes hacerme consultas legales o subir un documento PDF para analizarlo.',
  }])
  const [pregunta,    setPregunta]    = useState('')
  const [archivo,     setArchivo]     = useState(null)
  const [cargando,    setCargando]    = useState(false)
  const [subiendo,    setSubiendo]    = useState(false)
  const [darkMode,    setDarkMode]    = useState(false)
  const [convActiva,  setConvActiva]  = useState(1)
  const [convs,       setConvs]       = useState(CONVS_INICIALES)
  const [menuAbierto, setMenuAbierto] = useState(null)
  const [modalRename, setModalRename] = useState(null)
  const [nuevoNombre, setNuevoNombre] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const bottomRef = useRef(null)
  const fileRef   = useRef(null)

  // ── Verificar sesión activa al cargar ──
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUsuario(session?.user ?? null)
      setCargandoAuth(false)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUsuario(session?.user ?? null)
      }
    )
    return () => subscription.unsubscribe()
  }, [])

  useEffect(() => {
    document.body.classList.toggle('dark', darkMode)
  }, [darkMode])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mensajes, cargando])

  useEffect(() => {
    const cerrar = () => setMenuAbierto(null)
    document.addEventListener('click', cerrar)
    return () => document.removeEventListener('click', cerrar)
  }, [])

  const cerrarSesion = async () => {
    await supabase.auth.signOut()
    setUsuario(null)
  }

  // SESSION_ID real del usuario autenticado
  const SESSION_ID = usuario?.id ?? 'sesion-default'

  // ── Subir archivo ──
  const subirArchivo = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setSubiendo(true)
    setMensajes((m) => [...m, { rol: 'pdf', texto: file.name }])

    const form = new FormData()
    form.append('archivo',    file)
    form.append('session_id', SESSION_ID)

    try {
      const res  = await fetch(`${API}/subir-documento`, { method: 'POST', body: form })
      const data = await res.json()

      if (data.ok) {
        setArchivo(file.name)
        setMensajes((m) => [...m, {
          rol:   'bot',
          texto: 'Documento cargado correctamente. Ya puedes hacer consultas sobre él.',
        }])
      } else {
        setMensajes((m) => [...m, { rol: 'bot', texto: `Error: ${data.error}` }])
      }
    } catch {
      setMensajes((m) => [...m, {
        rol:   'bot',
        texto: 'No se pudo conectar con el servidor. Inténtalo nuevamente.',
      }])
    } finally {
      setSubiendo(false)
      e.target.value = ''
    }
  }

  // ── Enviar pregunta ──
  const enviar = async () => {
    if (!pregunta.trim() || cargando) return
    const preguntaActual = pregunta
    setPregunta('')
    setMensajes((m) => [...m, { rol: 'user', texto: preguntaActual }])
    setCargando(true)

    try {
      const form = new FormData()
      form.append('pregunta',   preguntaActual)
      form.append('session_id', SESSION_ID)

      const res  = await fetch(`${API}/preguntar`, { method: 'POST', body: form })
      const data = await res.json()

      setMensajes((m) => [...m, {
        rol:   'bot',
        texto: data.error
          ? data.error + (data.tip ? `\n\nSugerencia: ${data.tip}` : '')
          : data.respuesta,
      }])
    } catch {
      setMensajes((m) => [...m, {
        rol:   'bot',
        texto: 'No se pudo conectar con el servidor. Inténtalo nuevamente.',
      }])
    } finally {
      setCargando(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      enviar()
    }
  }

  const handleTextarea = (e) => {
    setPregunta(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`
  }

  const nuevaConversacion = () => {
    const nueva = { id: Date.now(), titulo: 'Nueva consulta', fecha: 'Hoy' }
    setConvs((c) => [nueva, ...c])
    setConvActiva(nueva.id)
    setMensajes([{
      rol:   'bot',
      texto: 'Nueva conversación iniciada. ¿En qué asunto legal puedo ayudarte?',
    }])
    setArchivo(null)
    setPregunta('')
    setSidebarOpen(false)
  }

  const seleccionarConversacion = (id) => {
    setConvActiva(id)
    setSidebarOpen(false)
  }

  const abrirMenu = (e, id) => {
    e.stopPropagation()
    setMenuAbierto(menuAbierto === id ? null : id)
  }

  const abrirRename = (e, conv) => {
    e.stopPropagation()
    setMenuAbierto(null)
    setModalRename(conv.id)
    setNuevoNombre(conv.titulo)
  }

  const confirmarRename = () => {
    if (!nuevoNombre.trim()) return
    setConvs((c) => c.map((conv) => (
      conv.id === modalRename ? { ...conv, titulo: nuevoNombre.trim() } : conv
    )))
    setModalRename(null)
    setNuevoNombre('')
  }

  const eliminarConv = (e, id) => {
    e.stopPropagation()
    setMenuAbierto(null)
    setConvs((c) => c.filter((conv) => conv.id !== id))
    if (convActiva === id) {
      setConvActiva(null)
      setMensajes([{ rol: 'bot', texto: 'Selecciona una conversación o crea una nueva.' }])
    }
  }

  const convActivaObj = convs.find((c) => c.id === convActiva)

  // ── Pantalla de carga ──
  if (cargandoAuth) {
    return (
      <div style={{
        minHeight:       '100vh',
        display:         'flex',
        alignItems:      'center',
        justifyContent:  'center',
        background:      '#f0f2f5'
      }}>
        <p style={{ color: '#6b7280', fontSize: '14px' }}>Cargando...</p>
      </div>
    )
  }

  // ── Pantalla de login ──
  if (!usuario) {
    return <Login onLogin={setUsuario} />
  }

  // ── App principal ──
  return (
    <div className="app">
      {sidebarOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="Cerrar navegación"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="brand-mark"><Icon name="scale" size={22} /></div>
          <div className="brand-copy">
            <p className="sidebar-title">LexPerú</p>
            <p className="sidebar-subtitle">Inteligencia jurídica</p>
          </div>
          <button
            className="mobile-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Cerrar menú"
          >
            <Icon name="close" />
          </button>
        </div>

        <button className="btn-new-chat" onClick={nuevaConversacion}>
          <span className="new-chat-icon"><Icon name="plus" size={17} /></span>
          Nueva consulta
        </button>

        <div className="sidebar-heading">
          <span>Conversaciones</span>
          <span className="conversation-count">{convs.length}</span>
        </div>

        <div className="sidebar-list">
          {convs.map((conv) => (
            <div
              key={conv.id}
              className={`sidebar-item ${convActiva === conv.id ? 'active' : ''}`}
              onClick={() => seleccionarConversacion(conv.id)}
            >
              <span className="sidebar-item-icon"><Icon name="chat" size={17} /></span>
              <span className="sidebar-item-content">
                <span className="sidebar-item-text">{conv.titulo}</span>
                <span className="sidebar-item-date">{conv.fecha}</span>
              </span>

              <button
                className="btn-three-dots"
                onClick={(e) => abrirMenu(e, conv.id)}
                aria-label={`Opciones de ${conv.titulo}`}
              >
                <Icon name="dots" size={19} />
              </button>

              {menuAbierto === conv.id && (
                <div className="dropdown" onClick={(e) => e.stopPropagation()}>
                  <button className="dropdown-item" onClick={(e) => abrirRename(e, conv)}>
                    <Icon name="edit" size={16} /> Renombrar
                  </button>
                  <button className="dropdown-item danger" onClick={(e) => eliminarConv(e, conv.id)}>
                    <Icon name="trash" size={16} /> Eliminar
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="sidebar-trust">
          <Icon name="shield" size={18} />
          <div>
            <strong>Entorno confidencial</strong>
            <span>Tus consultas se procesan de forma segura.</span>
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="profile-avatar">
            {usuario.email?.charAt(0).toUpperCase() ?? 'A'}
          </div>
          <div className="profile-copy">
            <strong>{usuario.email?.split('@')[0] ?? 'Abogado'}</strong>
            <span>{usuario.email}</span>
          </div>
          <button
            className="btn-dark"
            onClick={() => setDarkMode((d) => !d)}
            title={darkMode ? 'Usar modo claro' : 'Usar modo oscuro'}
          >
            <Icon name={darkMode ? 'sun' : 'moon'} size={18} />
          </button>
          <button
            className="btn-dark"
            onClick={cerrarSesion}
            title="Cerrar sesión"
          >
            <Icon name="logout" size={18} />
          </button>
        </div>
      </aside>

      <main className="chat-area">
        <header className="chat-header">
          <button
            className="mobile-menu"
            onClick={() => setSidebarOpen(true)}
            aria-label="Abrir menú"
          >
            <Icon name="menu" />
          </button>
          <div className="bot-avatar header-avatar"><Icon name="scale" size={19} /></div>
          <div className="chat-header-copy">
            <p className="chat-header-title">
              {archivo || convActivaObj?.titulo || 'Consulta legal'}
            </p>
            <p className="chat-header-sub">
              {archivo ? 'Documento listo para consulta' : 'Asistente especializado en derecho peruano'}
            </p>
          </div>
          <span className="badge-online"><i /> Disponible</span>
        </header>

        <section className="mensajes" aria-live="polite">
          <div className="messages-inner">
            <div className="conversation-intro">
              <span>Consulta privada</span>
              <p>Las respuestas son orientativas y no reemplazan el consejo de un abogado.</p>
            </div>

            {mensajes.map((m, i) => {
              if (m.rol === 'pdf') {
                return (
                  <div key={i} className="row-bot">
                    <div className="avatar-spacer" />
                    <div className="pdf-badge">
                      <span className="pdf-icon"><Icon name="file" size={18} /></span>
                      <span><strong>{m.texto}</strong><small>Documento PDF</small></span>
                    </div>
                  </div>
                )
              }

              if (m.rol === 'user') {
                return (
                  <div key={i} className="row-user">
                    <div className="bubble-user">{m.texto}</div>
                  </div>
                )
              }

              return (
                <div key={i} className="row-bot">
                  <div className="bot-avatar"><Icon name="scale" size={17} /></div>
                  <div className="message-content">
                    <span className="message-author">LexPerú</span>
                    <div className="bubble-bot">
                      {m.texto.split('\n').map((linea, j, lines) => (
                        <span key={j}>
                          {linea}
                          {j < lines.length - 1 && <br />}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })}

            {cargando && (
              <div className="row-bot">
                <div className="bot-avatar"><Icon name="scale" size={17} /></div>
                <div className="message-content">
                  <span className="message-author">Analizando consulta...</span>
                  <div className="bubble-bot typing-bubble">
                    <div className="typing"><span /><span /><span /></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </section>

        <footer className="input-area">
          <div className="composer">
            <textarea
              rows={1}
              value={pregunta}
              onChange={handleTextarea}
              onKeyDown={handleKeyDown}
              placeholder="Escribe tu consulta legal..."
              disabled={cargando}
              aria-label="Consulta legal"
            />
            <div className="composer-actions">
              <button
                className={`btn-attach ${subiendo ? 'active' : ''}`}
                onClick={() => fileRef.current.click()}
                title="Adjuntar documento PDF"
                disabled={subiendo}
              >
                {subiendo ? <span className="loader" /> : <Icon name="plus" size={19} />}
                <span className="attach-label">Adjuntar PDF</span>
              </button>
              <input
                ref={fileRef}
                type="file"
                accept=".pdf"
                onChange={subirArchivo}
                hidden
              />
              <span className="composer-hint">Enter para enviar · Shift + Enter para nueva línea</span>
              <button
                className="btn-send"
                onClick={enviar}
                disabled={cargando || !pregunta.trim()}
                aria-label="Enviar consulta"
              >
                <Icon name="send" size={18} />
              </button>
            </div>
          </div>
          <p className="legal-note">LexPerú puede cometer errores. Verifica la información legal relevante.</p>
        </footer>
      </main>

      {modalRename && (
        <div className="modal-overlay" onClick={() => setModalRename(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-icon"><Icon name="edit" size={20} /></div>
            <h3>Renombrar conversación</h3>
            <p>Usa un nombre breve que te ayude a identificar esta consulta.</p>
            <label htmlFor="conversation-name">Nombre de la conversación</label>
            <input
              id="conversation-name"
              type="text"
              value={nuevoNombre}
              onChange={(e) => setNuevoNombre(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && confirmarRename()}
              autoFocus
            />
            <div className="modal-btns">
              <button className="btn-cancel" onClick={() => setModalRename(null)}>Cancelar</button>
              <button className="btn-confirm" onClick={confirmarRename}>Guardar cambios</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}