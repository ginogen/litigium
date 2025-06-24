import { createClient } from '@supabase/supabase-js'

// Variables de entorno - se configurarán desde el backend o variables de entorno
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'http://localhost:8000/api/supabase-config'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

let supabase;

if (typeof window !== 'undefined' && supabaseUrl && supabaseAnonKey) {
  supabase = createClient(supabaseUrl, supabaseAnonKey)
} else if (typeof window !== 'undefined') {
  // Si no hay variables de entorno, obtener configuración del backend
  supabase = null; // Se inicializará dinámicamente
}

export { supabase }

// Función para inicializar Supabase dinámicamente
export async function initSupabase() {
  if (supabase) return supabase;
  
  try {
    // Obtener configuración del backend
    const response = await fetch('/api/v1/supabase-config');
    if (response.ok) {
      const config = await response.json();
      supabase = createClient(config.url, config.anon_key);
      return supabase;
    }
  } catch (error) {
    console.error('Error inicializando Supabase:', error);
  }
  
  return null;
}

// Funciones de autenticación
export const auth = {
  async signIn(email, password) {
    const client = await initSupabase();
    if (!client) throw new Error('Supabase no inicializado');
    
    const { data, error } = await client.auth.signInWithPassword({
      email,
      password
    });
    
    if (error) throw error;
    return data;
  },

  async signUp(email, password, userData = {}) {
    const client = await initSupabase();
    if (!client) throw new Error('Supabase no inicializado');
    
    const { data, error } = await client.auth.signUp({
      email,
      password,
      options: {
        data: userData
      }
    });
    
    if (error) throw error;
    return data;
  },

  async signOut() {
    const client = await initSupabase();
    if (!client) throw new Error('Supabase no inicializado');
    
    const { error } = await client.auth.signOut();
    if (error) throw error;
  },

  async getSession() {
    const client = await initSupabase();
    if (!client) return null;
    
    const { data } = await client.auth.getSession();
    return data.session;
  }
}; 