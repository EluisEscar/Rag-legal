import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import Login from './components/Login'
import { authenticatedFetch, authenticatedJson } from './services/api'
import { supabase } from './services/supabaseClient'
import './styles/App.css'

const API = 'http://localhost:8000'

const MENSAJE_INICIAL = {
  rol: 'bot',
  texto: 'Hola, soy Intilex, tu asistente legal inteligente especializado en derecho peruano. Puedes hacerme consultas sobre normativas, jurisprudencia o subir un documento PDF para que lo analicemos juntos. ¿En qué puedo ayudarte hoy?',
}

function formatearFecha(fecha) {
  if (!fecha) return ''

  const valor = new Date(fecha)
  const hoy = new Date()
  if (valor.toDateString() === hoy.toDateString()) return 'Hoy'

  return valor.toLocaleDateString('es-PE', {
    day: '2-digit',
    month: 'short',
  })
}

function convertirMensajes(historial) {
  return historial.map((mensaje) => ({
    rol: mensaje.role === 'user' ? 'user' : 'bot',
    texto: mensaje.content,
  }))
}

function claveConversacionActiva(userId) {
  return `intilex:conversacion-activa:${userId}`
}

function Icon({ name, size = 20 }) {
  const paths = {
    scale: (
      <>
        <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41" opacity="0.45" />
        <path d="M12 6v13M9 19h6M6 9.5h12M8 9.5l-2 4h4ZM16 9.5l-2 4h4Z" />
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
  const [mensajes,    setMensajes]    = useState([MENSAJE_INICIAL])
  const [pregunta,    setPregunta]    = useState('')
  const [archivo,     setArchivo]     = useState(null)
  const [cargando,    setCargando]    = useState(false)
  const [cargandoHistorial, setCargandoHistorial] = useState(false)
  const [subiendo,    setSubiendo]    = useState(false)
  const [darkMode,    setDarkMode]    = useState(
    () => {
      const temaGuardado = localStorage.getItem('intilex:tema')
      if (temaGuardado) return temaGuardado === 'dark'
      return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
    }
  )
  const [convActiva,  setConvActiva]  = useState(null)
  const [convs,       setConvs]       = useState([])
  const [menuAbierto, setMenuAbierto] = useState(null)
  const [modalRename, setModalRename] = useState(null)
  const [nuevoNombre, setNuevoNombre] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const bottomRef = useRef(null)
  const fileRef   = useRef(null)
  const historialesCache = useRef(new Map())
  const usuarioId = usuario?.id

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
    if (!usuarioId) {
      historialesCache.current.clear()
      setConvs([])
      setConvActiva(null)
      setMensajes([MENSAJE_INICIAL])
      return
    }

    let cancelado = false

    const cargarConversaciones = async () => {
      try {
        const conversaciones = await authenticatedJson(
          `${API}/conversaciones`
        )
        if (cancelado) return

        const normalizadas = conversaciones.map((conversacion) => ({
          ...conversacion,
          fecha: formatearFecha(
            conversacion.updated_at ?? conversacion.created_at
          ),
        }))
        setConvs(normalizadas)

        if (normalizadas.length > 0) {
          const idGuardado = localStorage.getItem(
            claveConversacionActiva(usuarioId)
          )
          const seleccionada = normalizadas.find(
            (conversacion) => conversacion.id === idGuardado
          ) ?? normalizadas[0]
          const historial = await authenticatedJson(
            `${API}/conversaciones/${seleccionada.id}/mensajes`
          )
          if (cancelado) return
          setConvActiva(seleccionada.id)
          localStorage.setItem(
            claveConversacionActiva(usuarioId),
            seleccionada.id
          )
          const mensajesIniciales = historial.length > 0
            ? convertirMensajes(historial)
            : [MENSAJE_INICIAL]
          historialesCache.current.set(
            seleccionada.id,
            mensajesIniciales
          )
          setMensajes([...mensajesIniciales])
        }
      } catch (error) {
        if (!cancelado) {
          setMensajes([{
            rol: 'bot',
            texto: `No se pudo cargar el historial: ${error.message}`,
          }])
        }
      }
    }

    cargarConversaciones()
    return () => {
      cancelado = true
    }
  }, [usuarioId])

  useEffect(() => {
    document.body.classList.toggle('dark', darkMode)
    localStorage.setItem('intilex:tema', darkMode ? 'dark' : 'light')
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

  const crearConversacion = async (titulo = 'Nueva consulta') => {
    const form = new FormData()
    form.append('titulo', titulo)
    const conversacion = await authenticatedJson(`${API}/conversaciones`, {
      method: 'POST',
      body: form,
    })
    const nueva = {
      ...conversacion,
      fecha: 'Hoy',
    }
    setConvs((actuales) => [nueva, ...actuales])
    setConvActiva(nueva.id)
    historialesCache.current.set(nueva.id, [])
    localStorage.setItem(
      claveConversacionActiva(usuario.id),
      nueva.id
    )
    return nueva
  }

  // ── Subir archivo ──
  const subirArchivo = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setSubiendo(true)
    setMensajes((m) => [...m, { rol: 'pdf', texto: file.name }])

    const form = new FormData()
    form.append('archivo', file)

    try {
      const res = await authenticatedFetch(`${API}/subir-documento`, {
        method: 'POST',
        body: form,
      })
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
    if (!pregunta.trim() || cargando || cargandoHistorial) return
    const preguntaActual = pregunta
    setPregunta('')
    const mensajeUsuario = { rol: 'user', texto: preguntaActual }
    setMensajes((actuales) => [...actuales, mensajeUsuario])
    setCargando(true)

    try {
      let conversacionId = convActiva
      if (!conversacionId) {
        const nueva = await crearConversacion()
        conversacionId = nueva.id
      }

      const form = new FormData()
      form.append('pregunta', preguntaActual)
      form.append('conversacion_id', conversacionId)

      const res = await authenticatedFetch(`${API}/preguntar`, {
        method: 'POST',
        body: form,
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail ?? err.error ?? 'Error del servidor')
      }

      // ── STREAMING ──
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let respuestaAcumulada = ''

      // Agrega burbuja vacía que iremos llenando
      setMensajes((m) => [...m, { rol: 'bot', texto: '' }])
      setCargando(false) // quitamos el "typing..." porque ya empieza a llegar texto

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const lineas = decoder.decode(value).split('\n').filter(Boolean)

        for (const linea of lineas) {
          const data = JSON.parse(linea)

          if (data.tipo === 'chunk') {
            respuestaAcumulada += data.texto
            // Actualiza el último mensaje (la burbuja del bot)
            const textoActual = respuestaAcumulada
            setMensajes((m) => {
              const copia = [...m]
              copia[copia.length - 1] = { rol: 'bot', texto: textoActual }
              return copia
            })
          }

          if (data.tipo === 'fin') {
            // Actualiza la caché local
            const mensajesActuales = historialesCache.current.get(conversacionId) ?? []
            historialesCache.current.set(conversacionId, [
              ...mensajesActuales,
              mensajeUsuario,
              { rol: 'bot', texto: respuestaAcumulada },
            ])
            setConvs((actuales) => {
              const activa = actuales.find((conv) => conv.id === conversacionId)
              if (!activa) return actuales
              return [
                { ...activa, fecha: 'Hoy' },
                ...actuales.filter((conv) => conv.id !== conversacionId),
              ]
            })
          }
        }
      }

    } catch (error) {
      setMensajes((m) => [...m, {
        rol: 'bot',
        texto: `No se pudo completar la consulta: ${error.message}`,
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

  const nuevaConversacion = async () => {
    try {
      const nueva = await crearConversacion()
      const mensajesNuevaConversacion = [{
        rol: 'bot',
        texto: 'Nueva conversación iniciada. ¿En qué asunto legal puedo ayudarte?',
      }]
      historialesCache.current.set(
        nueva.id,
        mensajesNuevaConversacion
      )
      setMensajes(mensajesNuevaConversacion)
      setArchivo(null)
      setPregunta('')
      setSidebarOpen(false)
    } catch (error) {
      setMensajes([{
        rol: 'bot',
        texto: `No se pudo crear la conversación: ${error.message}`,
      }])
    }
  }

  const seleccionarConversacion = async (id) => {
    if (id === convActiva || cargando || cargandoHistorial) return

    const historialCacheado = historialesCache.current.get(id)
    if (historialCacheado) {
      setConvActiva(id)
      localStorage.setItem(
        claveConversacionActiva(usuario.id),
        id
      )
      setMensajes([...historialCacheado])
      setSidebarOpen(false)
      return
    }

    setCargandoHistorial(true)
    try {
      const historial = await authenticatedJson(
        `${API}/conversaciones/${id}/mensajes`
      )
      setConvActiva(id)
      localStorage.setItem(
        claveConversacionActiva(usuario.id),
        id
      )
      const mensajesRecuperados = historial.length > 0
        ? convertirMensajes(historial)
        : [MENSAJE_INICIAL]
      historialesCache.current.set(id, mensajesRecuperados)
      setMensajes([...mensajesRecuperados])
      setSidebarOpen(false)
    } catch (error) {
      setMensajes([{
        rol: 'bot',
        texto: `No se pudo cargar la conversación: ${error.message}`,
      }])
    } finally {
      setCargandoHistorial(false)
    }
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

  const confirmarRename = async () => {
    if (!nuevoNombre.trim()) return
    const titulo = nuevoNombre.trim()

    try {
      const form = new FormData()
      form.append('titulo', titulo)
      await authenticatedJson(`${API}/conversaciones/${modalRename}`, {
        method: 'PUT',
        body: form,
      })
      setConvs((actuales) => actuales.map((conv) => (
        conv.id === modalRename ? { ...conv, titulo } : conv
      )))
      setModalRename(null)
      setNuevoNombre('')
    } catch (error) {
      setMensajes((actuales) => [...actuales, {
        rol: 'bot',
        texto: `No se pudo renombrar: ${error.message}`,
      }])
    }
  }

  const eliminarConv = async (e, id) => {
    e.stopPropagation()
    setMenuAbierto(null)

    try {
      await authenticatedJson(`${API}/conversaciones/${id}`, {
        method: 'DELETE',
      })
      setConvs((actuales) => actuales.filter((conv) => conv.id !== id))
      historialesCache.current.delete(id)
      if (convActiva === id) {
        setConvActiva(null)
        localStorage.removeItem(
          claveConversacionActiva(usuario.id)
        )
        setMensajes([{
          rol: 'bot',
          texto: 'Selecciona una conversación o crea una nueva.',
        }])
      }
    } catch (error) {
      setMensajes((actuales) => [...actuales, {
        rol: 'bot',
        texto: `No se pudo eliminar: ${error.message}`,
      }])
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
            <p className="sidebar-title">Intilex</p>
            <p className="sidebar-subtitle">RAG Legal Peruano</p>
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
            {(usuario.user_metadata?.full_name ?? usuario.email)
              ?.charAt(0)
              .toUpperCase() ?? 'A'}
          </div>
          <div className="profile-copy">
            <strong>
              {usuario.user_metadata?.full_name
                ?? usuario.email?.split('@')[0]
                ?? 'Abogado'}
            </strong>
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
              {archivo ? 'Documento listo para consulta' : 'RAG Legal Peruano'}
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
                    <span className="message-author">Intilex</span>
                    <div className="bubble-bot">
                      <ReactMarkdown>{m.texto}</ReactMarkdown>
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
              disabled={cargando || cargandoHistorial}
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
                disabled={cargando || cargandoHistorial || !pregunta.trim()}
                aria-label="Enviar consulta"
              >
                <Icon name="send" size={18} />
              </button>
            </div>
          </div>
          <p className="legal-note">Intilex puede cometer errores de análisis. Verifica siempre la información jurídica relevante.</p>
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
