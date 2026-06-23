import { useEffect, useMemo, useState } from 'react'
import { supabase } from '../services/supabaseClient'
import '../styles/Login.css'

const REQUISITOS_PASSWORD = [
  { id: 'longitud', texto: '8 caracteres como mínimo', validar: (value) => value.length >= 8 },
  { id: 'mayuscula', texto: 'Una letra mayúscula', validar: (value) => /[A-ZÁÉÍÓÚÑ]/.test(value) },
  { id: 'numero', texto: 'Un número', validar: (value) => /\d/.test(value) },
  { id: 'especial', texto: 'Un carácter especial', validar: (value) => /[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]/.test(value) },
]

function Icon({ name, size = 20 }) {
  if (name === 'google') {
    return (
      <svg
        aria-hidden="true"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="icon"
      >
        <path fill="#4285F4" d="M24 12.28c0-.85-.07-1.68-.21-2.48H12v4.7h6.63c-.29 1.54-1.16 2.84-2.48 3.73v3.13h3.97c2.32-2.14 3.66-5.29 3.66-9.08z" />
        <path fill="#34A853" d="M12 24c3.31 0 6.09-1.1 8.11-2.98l-3.97-3.13c-1.1.74-2.51 1.17-4.14 1.17-3.18 0-5.87-2.15-6.83-5.04H1.05v3.23C3.1 21.05 7.15 24 12 24z" />
        <path fill="#FBBC05" d="M5.17 14.02c-.25-.74-.39-1.54-.39-2.36s.14-1.62.39-2.36V6.07H1.05C.38 7.41 0 8.93 0 10.53s.38 3.12 1.05 4.46l4.12-3.23z" />
        <path fill="#EA4335" d="M12 4.79c1.74 0 3.3.6 4.53 1.77l3.4-3.4C17.75 1.1 15.17 0 12 0 7.15 0 3.1 2.95 1.05 7.07l4.12 3.23c.96-2.89 3.65-5.04 6.83-5.04z" />
      </svg>
    )
  }

  const paths = {
    scale: (
      <>
        <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41" opacity="0.45" />
        <path d="M12 6v13M9 19h6M6 9.5h12M8 9.5l-2 4h4ZM16 9.5l-2 4h4Z" />
      </>
    ),
    eye: (
      <>
        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
        <circle cx="12" cy="12" r="2.5" />
      </>
    ),
    eyeOff: (
      <>
        <path d="m3 3 18 18" />
        <path d="M10.6 6.2A9.8 9.8 0 0 1 12 6c6.5 0 10 6 10 6a17.7 17.7 0 0 1-2.1 2.9M6.5 6.5C3.6 8.4 2 12 2 12s3.5 6 10 6c1.7 0 3.2-.4 4.5-1" />
        <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
      </>
    ),
    shield: (
      <>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
    file: (
      <>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
        <path d="M14 2v6h6M8 13h8M8 17h5" />
      </>
    ),
    chat: <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8Z" />,
    check: <path d="m5 12 4 4L19 6" />,
    arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
    arrowLeft: <path d="M19 12H5M11 18l-6-6 6-6" />,
    menu: <path d="M4 7h16M4 12h16M4 17h16" />,
    close: <path d="m6 6 12 12M18 6 6 18" />,
    moon: <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z" />,
    sun: (
      <>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41" />
      </>
    ),
  }

  return (
    <svg
      aria-hidden="true"
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

export default function Login({ onLogin }) {
  const [nombre, setNombre] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mostrarPassword, setMostrarPassword] = useState(false)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [modo, setModo] = useState('login')
  const [menuAbierto, setMenuAbierto] = useState(false)
  const [darkMode, setDarkMode] = useState(() => {
    const temaGuardado = localStorage.getItem('intilex:tema')
    if (temaGuardado) return temaGuardado === 'dark'
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
  })
  const [vista, setVista] = useState(
    window.location.hash === '#/registro' || window.location.hash === '#/login'
      ? 'auth'
      : 'landing'
  )

  const requisitos = useMemo(
    () => REQUISITOS_PASSWORD.map((requisito) => ({
      ...requisito,
      cumplido: requisito.validar(password),
    })),
    [password]
  )
  const passwordValida = requisitos.every((requisito) => requisito.cumplido)

  useEffect(() => {
    document.body.classList.toggle('dark', darkMode)
    localStorage.setItem('intilex:tema', darkMode ? 'dark' : 'light')
  }, [darkMode])

  useEffect(() => {
    const sincronizarVista = () => {
      const hash = window.location.hash
      if (hash === '#/registro') {
        setModo('registro')
        setError('')
        setMensaje('')
        setPassword('')
        setMostrarPassword(false)
        setVista('auth')
      } else if (hash === '#/login') {
        setModo('login')
        setError('')
        setMensaje('')
        setPassword('')
        setMostrarPassword(false)
        setVista('auth')
      } else {
        setVista('landing')
      }
    }

    window.addEventListener('hashchange', sincronizarVista)
    return () => window.removeEventListener('hashchange', sincronizarVista)
  }, [])

  const cambiarModo = (nuevoModo) => {
    setModo(nuevoModo)
    setError('')
    setMensaje('')
    setPassword('')
    setMostrarPassword(false)
  }

  const irAlAcceso = (nuevoModo = 'login') => {
    cambiarModo(nuevoModo)
    setMenuAbierto(false)
    setVista('auth')
    window.location.hash = nuevoModo === 'registro' ? '#/registro' : '#/login'
  }

  const manejarSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setMensaje('')

    if (!email.trim() || !password) {
      setError('Completa tu correo y contraseña.')
      return
    }
    if (modo === 'registro' && !nombre.trim()) {
      setError('Ingresa tu nombre para crear la cuenta.')
      return
    }
    if (modo === 'registro' && !passwordValida) {
      setError('Tu contraseña todavía no cumple todos los requisitos.')
      return
    }

    setCargando(true)
    try {
      const resultado = modo === 'login'
        ? await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        })
        : await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: {
            data: {
              nombre: nombre.trim(),
              full_name: nombre.trim(),
            },
          },
        })

      if (resultado.error) {
        console.warn('Error de autenticacion Supabase', resultado.error)
        setError(traducirError(resultado.error))
      } else if (resultado.data.session) {
        onLogin(resultado.data.user)
      } else {
        setMensaje(
          'Cuenta creada. Revisa tu correo para confirmar el registro antes de iniciar sesión.'
        )
        setModo('login')
        setPassword('')
      }
    } catch {
      setError('No pudimos conectar con el servicio. Inténtalo nuevamente.')
    } finally {
      setCargando(false)
    }
  }

  const manejarGoogleLogin = async () => {
    setError('')
    setMensaje('')
    setCargando(true)
    try {
      const { error: oauthError } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin,
        }
      })
      if (oauthError) {
        console.warn('Error de OAuth Supabase', oauthError)
        setError(traducirError(oauthError))
      }
    } catch {
      setError('No se pudo iniciar la autenticación con Google. Inténtalo de nuevo.')
    } finally {
      setCargando(false)
    }
  }

  if (vista === 'auth') {
    return (
      <AuthScreen
        modo={modo}
        nombre={nombre}
        email={email}
        password={password}
        mostrarPassword={mostrarPassword}
        cargando={cargando}
        error={error}
        mensaje={mensaje}
        requisitos={requisitos}
        onNombreChange={setNombre}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onTogglePassword={() => setMostrarPassword((visible) => !visible)}
        onModoChange={(nuevoModo) => irAlAcceso(nuevoModo)}
        onSubmit={manejarSubmit}
        onBack={() => {
          setVista('landing')
          window.location.hash = ''
        }}
        darkMode={darkMode}
        onToggleTheme={() => setDarkMode((actual) => !actual)}
        onGoogleSubmit={manejarGoogleLogin}
      />
    )
  }

  return (
    <div className="landing-page">
      <header className="landing-nav">
        <a className="landing-brand" href="#inicio" aria-label="Intilex, inicio">
          <span className="landing-brand-mark"><Icon name="scale" size={21} /></span>
          <span>
            <strong>Intilex</strong>
            
          </span>
        </a>

        <nav className={`landing-links ${menuAbierto ? 'open' : ''}`}>
          <a href="#como-funciona" onClick={() => setMenuAbierto(false)}>Cómo funciona</a>
          <a href="#planes" onClick={() => setMenuAbierto(false)}>Planes</a>
          <button className="nav-login" onClick={() => irAlAcceso('login')}>
            Iniciar sesión
          </button>
          <button className="nav-cta" onClick={() => irAlAcceso('registro')}>
            Crear cuenta
          </button>
          <button
            className="theme-toggle"
            onClick={() => setDarkMode((actual) => !actual)}
            aria-label={darkMode ? 'Usar modo claro' : 'Usar modo oscuro'}
            title={darkMode ? 'Usar modo claro' : 'Usar modo oscuro'}
          >
            <Icon name={darkMode ? 'sun' : 'moon'} size={18} />
          </button>
        </nav>

        <button
          className="landing-menu"
          onClick={() => setMenuAbierto((abierto) => !abierto)}
          aria-label={menuAbierto ? 'Cerrar menú' : 'Abrir menú'}
        >
          <Icon name={menuAbierto ? 'close' : 'menu'} />
        </button>
      </header>

      <main>
        <section className="landing-hero" id="inicio">
          <div className="hero-copy">
            <span className="hero-kicker">
              <Icon name="shield" size={16} />
              Asistencia legal para el contexto peruano
            </span>
            <h1>Investiga, analiza y conversa con tus documentos legales.</h1>
            <p className="hero-description">
              Intilex combina una base jurídica de alta precisión con inteligencia
              artificial especializada en el derecho peruano para ayudarte a encontrar contexto,
              analizar PDFs y organizar cada consulta en un solo espacio.
            </p>
            <div className="hero-actions">
              <button className="hero-primary" onClick={() => irAlAcceso('registro')}>
                Comenzar gratis <Icon name="arrow" size={18} />
              </button>
              <a className="hero-secondary" href="#como-funciona">Ver cómo funciona</a>
            </div>
            <div className="hero-trust">
              <span><Icon name="check" size={15} /> Consultas organizadas</span>
              <span><Icon name="check" size={15} /> Documentos PDF</span>
              <span><Icon name="check" size={15} /> Acceso seguro</span>
            </div>
          </div>

          <div className="product-preview" aria-label="Vista previa de Intilex">
            <div className="preview-topbar">
              <div className="preview-brand">
                <span><Icon name="scale" size={15} /></span>
                Intilex
              </div>
              <span className="preview-status"><i /> Disponible</span>
            </div>
            <div className="preview-body">
              <aside className="preview-sidebar">
                <div className="preview-new">+ Nueva consulta</div>
                <small>CONVERSACIONES</small>
                <div className="preview-conversation active">
                  <Icon name="chat" size={14} /> Contrato laboral
                </div>
                <div className="preview-conversation">
                  <Icon name="chat" size={14} /> Derechos del consumidor
                </div>
                <div className="preview-conversation">
                  <Icon name="chat" size={14} /> Revisión de cláusulas
                </div>
              </aside>
              <div className="preview-chat">
                <div className="preview-date">Consulta privada</div>
                <div className="preview-user">
                  ¿Qué requisitos debe cumplir este contrato?
                </div>
                <div className="preview-answer">
                  <span className="preview-avatar"><Icon name="scale" size={14} /></span>
                  <div>
                    <strong>Intilex</strong>
                    <p>
                      Revisaré las cláusulas relevantes y las contrastaré con
                      el marco laboral peruano aplicable.
                    </p>
                    <div className="preview-source">
                      <Icon name="file" size={14} /> contrato_laboral.pdf
                    </div>
                  </div>
                </div>
                <div className="preview-input">
                  Escribe tu consulta legal...
                  <span>Enviar</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="landing-section how-section" id="como-funciona">
          <div className="section-heading">
            <span>UN FLUJO SIMPLE</span>
            <h2>De la pregunta al contexto legal en tres pasos</h2>
            <p>
              Diseñado para reducir el tiempo de búsqueda sin perder de vista
              las fuentes y el historial de cada asunto.
            </p>
          </div>
          <div className="steps-grid">
            <Step number="01" icon="file" title="Adjunta o consulta">
              Sube un PDF para analizarlo o pregunta directamente sobre derecho peruano.
            </Step>
            <Step number="02" icon="scale" title="Encuentra contexto">
              Intilex busca fragmentos relevantes y organiza la información útil.
            </Step>
            <Step number="03" icon="chat" title="Continúa la conversación">
              Conserva cada historial, retoma preguntas y separa tus asuntos.
            </Step>
          </div>
        </section>

        <section className="landing-section plans-section" id="planes">
          <div className="section-heading">
            <span>PLANES CLAROS</span>
            <h2>Empieza gratis. Escala cuando lo necesites.</h2>
            <p>Sin configuraciones complejas y con acceso desde cualquier navegador.</p>
          </div>
          <div className="plans-grid">
            <Plan
              label="FREE"
              title="Para comenzar"
              description="Explora la plataforma y organiza tus primeras consultas."
              price="S/ 0"
              period="para siempre"
              features={[
                'Consultas legales básicas',
                'Historial de conversaciones',
                'Acceso a la base legal',
                'Carga limitada de PDFs',
              ]}
              button="Crear cuenta gratis"
              onClick={() => irAlAcceso('registro')}
            />
            <Plan
              featured
              label="PROFESIONAL"
              title="Para trabajar sin límites"
              description="Más capacidad para profesionales y consultas frecuentes."
              price="S/ 20"
              period="por mes"
              features={[
                'Todo lo incluido en Free',
                'Más consultas mensuales',
                'Mayor capacidad de documentos',
                'Acceso prioritario a nuevas funciones',
              ]}
              button="En Proceso"
              onClick={() => irAlAcceso('registro')}
            />
          </div>
        </section>

      </main>

      <footer className="landing-footer">
        <a className="landing-brand footer-brand" href="#inicio">
          <span className="landing-brand-mark"><Icon name="scale" size={18} /></span>
          <span><strong>Intilex</strong></span>
        </a>
        <p>Asistencia legal inteligente para profesionales y ciudadanos.</p>
        <span>© 2026 Intilex</span>
      </footer>
    </div>
  )
}

function AuthScreen({
  modo,
  nombre,
  email,
  password,
  mostrarPassword,
  cargando,
  error,
  mensaje,
  requisitos,
  onNombreChange,
  onEmailChange,
  onPasswordChange,
  onTogglePassword,
  onModoChange,
  onSubmit,
  onBack,
  darkMode,
  onToggleTheme,
  onGoogleSubmit,
}) {
  return (
    <div className="auth-page">
      <div className="auth-page-glow" />
      <header className="auth-page-header">
        <button className="auth-back" onClick={onBack}>
          <Icon name="arrowLeft" size={18} />
          Volver al inicio
        </button>
        <button
          className="theme-toggle auth-theme-toggle"
          onClick={onToggleTheme}
          aria-label={darkMode ? 'Usar modo claro' : 'Usar modo oscuro'}
          title={darkMode ? 'Usar modo claro' : 'Usar modo oscuro'}
        >
          <Icon name={darkMode ? 'sun' : 'moon'} size={18} />
        </button>
      </header>

      <main className="auth-page-main">
        <section className="auth-page-copy">
          <span className="hero-kicker">
            <Icon name="shield" size={16} />
            Acceso seguro
          </span>
          <h1>
            Tu espacio de trabajo legal, siempre disponible.
          </h1>
          <p>
            Recupera tus conversaciones, documentos y consultas en una
            experiencia privada y organizada.
          </p>
          <div className="auth-page-features">
            <span><Icon name="check" size={16} /> Historial por conversación</span>
            <span><Icon name="check" size={16} /> Acceso protegido con Supabase</span>
            <span><Icon name="check" size={16} /> Consulta legal y análisis de PDFs</span>
          </div>
        </section>

        <div className="auth-card auth-card-standalone">
          <div className="auth-heading">
            <span className="auth-logo"><Icon name="shield" size={22} /></span>
            <div>
              <h2>{modo === 'login' ? 'Bienvenido de vuelta' : 'Crea tu cuenta'}</h2>
              <p>
                {modo === 'login'
                  ? 'Ingresa para continuar con tus consultas.'
                  : 'Completa tus datos para comenzar gratis.'}
              </p>
            </div>
          </div>

          <div className="login-tabs">
            <button
              type="button"
              className={`login-tab ${modo === 'login' ? 'active' : ''}`}
              onClick={() => onModoChange('login')}
            >
              Iniciar sesión
            </button>
            <button
              type="button"
              className={`login-tab ${modo === 'registro' ? 'active' : ''}`}
              onClick={() => onModoChange('registro')}
            >
              Registrarse
            </button>
          </div>

          <form className="login-form" onSubmit={onSubmit}>
            {modo === 'registro' && (
              <div className="login-field">
                <label htmlFor="nombre">Nombre completo</label>
                <input
                  id="nombre"
                  type="text"
                  autoComplete="name"
                  placeholder="María Rodríguez"
                  value={nombre}
                  onChange={(event) => onNombreChange(event.target.value)}
                />
              </div>
            )}

            <div className="login-field">
              <label htmlFor="email">Correo electrónico</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="abogado@estudio.com"
                value={email}
                onChange={(event) => onEmailChange(event.target.value)}
              />
            </div>

            <div className="login-field">
              <label htmlFor="password">Contraseña</label>
              <div className="password-control">
                <input
                  id="password"
                  type={mostrarPassword ? 'text' : 'password'}
                  autoComplete={modo === 'login' ? 'current-password' : 'new-password'}
                  placeholder="Ingresa tu contraseña"
                  value={password}
                  onChange={(event) => onPasswordChange(event.target.value)}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={onTogglePassword}
                  aria-label={mostrarPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                >
                  <Icon name={mostrarPassword ? 'eye' : 'eyeOff'} size={19} />
                </button>
              </div>
            </div>

            {modo === 'registro' && (
              <div className="password-requirements">
                <strong>Requisitos de la contraseña</strong>
                <div className="requirements-grid">
                  {requisitos.map((requisito) => (
                    <span
                      key={requisito.id}
                      className={requisito.cumplido ? 'complete' : ''}
                    >
                      <i><Icon name="check" size={12} /></i>
                      {requisito.texto}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {error && <p className="login-message error">{error}</p>}
            {mensaje && <p className="login-message success">{mensaje}</p>}

            <button className="login-btn" type="submit" disabled={cargando}>
              {cargando
                ? 'Procesando...'
                : modo === 'login' ? 'Ingresar a Intilex' : 'Crear cuenta gratis'}
              {!cargando && <Icon name="arrow" size={18} />}
            </button>
          </form>

          <div className="auth-divider">
            <span>o continuar con</span>
          </div>

          <button
            type="button"
            className="btn-google"
            onClick={onGoogleSubmit}
            disabled={cargando}
          >
            <Icon name="google" size={18} />
            {modo === 'login' ? 'Conectarse con Google' : 'Registrarse con Google'}
          </button>

          <p className="auth-legal">
            Las respuestas son orientativas y no reemplazan asesoría profesional.
          </p>
        </div>
      </main>
    </div>
  )
}

function Step({ number, icon, title, children }) {
  return (
    <article className="step-card">
      <span className="step-number">{number}</span>
      <div className="step-icon"><Icon name={icon} /></div>
      <h3>{title}</h3>
      <p>{children}</p>
    </article>
  )
}

function Plan({
  featured = false,
  label,
  title,
  description,
  price,
  period,
  features,
  button,
  onClick,
}) {
  return (
    <article className={`plan-card ${featured ? 'featured' : ''}`}>
      {featured && <span className="featured-badge">RECOMENDADO</span>}
      <div>
        <span className="plan-label">{label}</span>
        <h3>{title}</h3>
        <p className="plan-copy">{description}</p>
      </div>
      <div className="plan-price">
        <strong>{price}</strong>
        <span>{period}</span>
      </div>
      <ul>
        {features.map((feature) => (
          <li key={feature}><Icon name="check" size={16} /> {feature}</li>
        ))}
      </ul>
      <button
        className={`plan-button ${featured ? 'primary' : 'secondary'}`}
        onClick={onClick}
      >
        {button}
      </button>
    </article>
  )
}

function traducirError(error) {
  const message = obtenerMensajeError(error)
  const normalizado = message.toLowerCase()
  if (normalizado.includes('invalid login credentials')) {
    return 'El correo o la contraseña no son correctos.'
  }
  if (normalizado.includes('user already registered')) {
    return 'Ya existe una cuenta registrada con este correo.'
  }
  if (normalizado.includes('email not confirmed')) {
    return 'Confirma tu correo antes de iniciar sesión.'
  }
  if (normalizado.includes('password')) {
    return 'La contraseña no cumple los requisitos de seguridad.'
  }
  if (
    normalizado.includes('no api key found') ||
    normalizado.includes('apikey')
  ) {
    return 'No se encontró la clave pública de Supabase en el frontend. Reconstruye el contenedor y verifica SUPABASE_ANON_KEY.'
  }
  if (
    normalizado === '{}' ||
    normalizado.includes('failed to fetch') ||
    normalizado.includes('network')
  ) {
    return 'No pudimos conectar con Supabase. Verifica la configuración del proyecto y vuelve a intentarlo.'
  }
  return message
}

function obtenerMensajeError(error) {
  if (!error) {
    return 'No pudimos completar la autenticación.'
  }

  if (typeof error === 'string') {
    return error
  }

  if (typeof error.message === 'string' && error.message.trim()) {
    return error.message
  }

  if (typeof error.error_description === 'string' && error.error_description.trim()) {
    return error.error_description
  }

  if (typeof error.error === 'string' && error.error.trim()) {
    return error.error
  }

  try {
    const serializado = JSON.stringify(error)
    if (serializado && serializado !== '{}') {
      return serializado
    }
  } catch {
    // Ignoramos errores de serializacion para mostrar un fallback legible.
  }

  return 'No pudimos conectar con Supabase. Verifica la configuración del proyecto y vuelve a intentarlo.'
}
