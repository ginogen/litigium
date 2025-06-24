// Función mejorada para obtener el token de Supabase
export const getAuthToken = async (): Promise<string | null> => {
  try {
    // Método: Buscar en localStorage con patrón de Supabase
    const keys = Object.keys(localStorage);
    const authKey = keys.find(key => 
      key.startsWith('sb-') && key.includes('-auth-token')
    );
    
    if (authKey) {
      const sessionData = localStorage.getItem(authKey);
      if (sessionData) {
        const parsed = JSON.parse(sessionData);
        return parsed.access_token;
      }
    }

    return null;
  } catch (error) {
    console.warn('Error obteniendo token de autenticación:', error);
    return null;
  }
};

// Configuración de headers con autenticación
export const getAuthHeaders = async (): Promise<Record<string, string>> => {
  const token = await getAuthToken();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
};

// Hook para verificar si el usuario está autenticado
export const isAuthenticated = async (): Promise<boolean> => {
  const token = await getAuthToken();
  return !!token;
}; 