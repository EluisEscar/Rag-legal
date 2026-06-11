import { supabase } from './supabaseClient'


export async function authenticatedFetch(url, options = {}) {
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error('No hay una sesion autenticada')
  }

  const headers = new Headers(options.headers ?? {})
  headers.set('Authorization', `Bearer ${session.access_token}`)

  return fetch(url, {
    ...options,
    headers,
  })
}


export async function authenticatedJson(url, options = {}) {
  const response = await authenticatedFetch(url, options)
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.detail ?? data.error ?? 'Error del servidor')
  }

  return data
}
