import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { createClient, User, Session } from '@supabase/supabase-js';
import { SupabaseError } from '@/components/Auth/SupabaseError';

// Configuración de Supabase
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Valores por defecto para desarrollo (reemplazar con tus valores reales)
const defaultUrl = 'https://your-project-id.supabase.co';
const defaultKey = 'your-anon-key-here';

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('⚠️ Variables de entorno de Supabase no encontradas. Usando valores por defecto.');
  console.warn('Por favor, crea un archivo .env en la carpeta frontend/ con:');
  console.warn('VITE_SUPABASE_URL=https://your-project-id.supabase.co');
  console.warn('VITE_SUPABASE_ANON_KEY=your_anon_key_here');
}

export const supabase = createClient(
  supabaseUrl || defaultUrl, 
  supabaseAnonKey || defaultKey
);

// Tipos
export interface UserProfile {
  id: string;
  user_id: string;
  nombre_completo: string;
  dni?: string;
  matricula_profesional: string;
  colegio_abogados?: string;
  email: string;
  telefono?: string;
  domicilio_profesional?: string;
  ciudad?: string;
  provincia?: string;
  codigo_postal?: string;
  especialidad: string[];
  anos_experiencia: number;
  universidad?: string;
  ano_graduacion?: number;
  tribunal_predeterminado?: string;
  formato_demanda_preferido: string;
  created_at: string;
  updated_at: string;
  activo: boolean;
}

interface AuthState {
  user: User | null;
  profile: UserProfile | null;
  session: Session | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isSupabaseConfigured: boolean;
}

interface AuthContextType extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, profileData: Partial<UserProfile>) => Promise<void>;
  signOut: () => Promise<void>;
  updateProfile: (data: Partial<UserProfile>) => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider
interface AuthProviderProps {
  children: ReactNode;
}

// Verificar si Supabase está configurado correctamente
const isSupabaseConfigured = supabaseUrl && supabaseAnonKey && 
  supabaseUrl !== defaultUrl && supabaseAnonKey !== defaultKey;

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    user: null,
    profile: null,
    session: null,
    isLoading: true,
    isAuthenticated: false,
    isSupabaseConfigured,
  });

  // Cargar perfil del usuario
  const loadUserProfile = async (userId: string): Promise<UserProfile | null> => {
    try {
      // Agregar timeout para evitar requests colgados
      const { data, error } = await Promise.race([
        supabase
          .from('abogados')
          .select('*')
          .eq('user_id', userId)
          .single(),
        new Promise<never>((_, reject) => 
          setTimeout(() => reject(new Error('Timeout cargando perfil')), 8000)
        )
      ]);

      if (error) {
        console.error('Error loading profile:', error);
        return null;
      }

      return data;
    } catch (error: any) {
      console.error('Error loading profile:', error);
      if (error.message === 'Timeout cargando perfil') {
        console.warn('⚠️ Timeout cargando perfil de usuario');
      }
      return null;
    }
  };

  // Actualizar estado de autenticación
  const updateAuthState = async (session: Session | null) => {
    if (session?.user) {
      const profile = await loadUserProfile(session.user.id);
      setState({
        user: session.user,
        profile,
        session,
        isLoading: false,
        isAuthenticated: true,
        isSupabaseConfigured,
      });
    } else {
      setState({
        user: null,
        profile: null,
        session: null,
        isLoading: false,
        isAuthenticated: false,
        isSupabaseConfigured,
      });
    }
  };

  // Inicializar autenticación
  useEffect(() => {
    // Obtener sesión inicial
    supabase.auth.getSession().then(({ data: { session } }) => {
      updateAuthState(session);
    });

    // Escuchar cambios de autenticación
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('Auth state changed:', event, session?.user?.email);
      await updateAuthState(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Iniciar sesión
  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      throw error;
    }
  };

  // Registrarse
  const signUp = async (email: string, password: string, profileData: Partial<UserProfile> = {}) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      throw error;
    }

    // El perfil se crea automáticamente mediante trigger
    // No necesitamos crear manualmente el perfil aquí
    console.log('Usuario registrado exitosamente. Perfil creado automáticamente.');
  };

  // Cerrar sesión
  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) {
      throw error;
    }
  };

  // Actualizar perfil
  const updateProfile = async (data: Partial<UserProfile>) => {
    if (!state.user) {
      throw new Error('No user logged in');
    }

    const { error } = await supabase
      .from('abogados')
      .update({
        ...data,
        updated_at: new Date().toISOString(),
      })
      .eq('user_id', state.user.id);

    if (error) {
      throw error;
    }

    // Recargar perfil
    await refreshProfile();
  };

  // Refrescar perfil
  const refreshProfile = async () => {
    if (!state.user) return;

    const profile = await loadUserProfile(state.user.id);
    setState(prev => ({
      ...prev,
      profile,
    }));
  };

  const value: AuthContextType = {
    ...state,
    signIn,
    signUp,
    signOut,
    updateProfile,
    refreshProfile,
  };

  // Mostrar error de configuración si Supabase no está configurado
  if (!state.isSupabaseConfigured) {
    return <SupabaseError />;
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook personalizado
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 