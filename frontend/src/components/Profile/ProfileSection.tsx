import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '@/utils';
import { User, Mail, Phone, MapPin, GraduationCap, Calendar, Save, Edit, Eye, EyeOff } from 'lucide-react';

export function ProfileSection() {
  const { profile, updateProfile, refreshProfile } = useAuth();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    nombre_completo: '',
    matricula_profesional: '',
    colegio_abogados: '',
    telefono: '',
    domicilio_profesional: '',
    ciudad: '',
    provincia: '',
    codigo_postal: '',
    especialidad: [] as string[],
    anos_experiencia: 0,
    universidad: '',
    ano_graduacion: undefined as number | undefined,
    tribunal_predeterminado: '',
    formato_demanda_preferido: 'formal',
  });

  // Mutation para actualizar perfil
  const updateProfileMutation = useMutation({
    mutationFn: async (profileData: typeof formData) => {
      return await updateProfile(profileData);
    },
    onSuccess: () => {
      setIsEditing(false);
      // Invalidar queries relacionadas al perfil si las hay
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: (error: any) => {
      console.error('Error updating profile:', error);
      if (error.message === 'Timeout guardando perfil') {
        alert('La operación está tardando demasiado. Intenta de nuevo.');
      } else {
        alert('Error guardando el perfil. Intenta de nuevo.');
      }
    }
  });

  // Cargar datos del perfil al montar
  useEffect(() => {
    if (profile) {
      setFormData({
        nombre_completo: profile.nombre_completo || '',
        matricula_profesional: profile.matricula_profesional || '',
        colegio_abogados: profile.colegio_abogados || '',
        telefono: profile.telefono || '',
        domicilio_profesional: profile.domicilio_profesional || '',
        ciudad: profile.ciudad || '',
        provincia: profile.provincia || '',
        codigo_postal: profile.codigo_postal || '',
        especialidad: profile.especialidad || [],
        anos_experiencia: profile.anos_experiencia || 0,
        universidad: profile.universidad || '',
        ano_graduacion: profile.ano_graduacion || undefined,
        tribunal_predeterminado: profile.tribunal_predeterminado || '',
        formato_demanda_preferido: profile.formato_demanda_preferido || 'formal',
      });
    }
    
    // Cleanup function para resetear estados al desmontar
    return () => {
      setIsEditing(false);
    };
  }, [profile]);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSpecialtyChange = (specialties: string) => {
    const specialtyArray = specialties.split(',').map(s => s.trim()).filter(s => s);
    handleInputChange('especialidad', specialtyArray);
  };

  const handleSave = async () => {
    updateProfileMutation.mutate(formData);
  };

  const handleCancel = () => {
    // Resetear formulario a los datos originales del perfil
    if (profile) {
      setFormData({
        nombre_completo: profile.nombre_completo || '',
        matricula_profesional: profile.matricula_profesional || '',
        colegio_abogados: profile.colegio_abogados || '',
        telefono: profile.telefono || '',
        domicilio_profesional: profile.domicilio_profesional || '',
        ciudad: profile.ciudad || '',
        provincia: profile.provincia || '',
        codigo_postal: profile.codigo_postal || '',
        especialidad: profile.especialidad || [],
        anos_experiencia: profile.anos_experiencia || 0,
        universidad: profile.universidad || '',
        ano_graduacion: profile.ano_graduacion || undefined,
        tribunal_predeterminado: profile.tribunal_predeterminado || '',
        formato_demanda_preferido: profile.formato_demanda_preferido || 'formal',
      });
    }
    setIsEditing(false);
  };

  const completionPercentage = React.useMemo(() => {
    const fields = [
      formData.nombre_completo,
      formData.matricula_profesional,
      formData.colegio_abogados,
      formData.telefono,
      formData.domicilio_profesional,
      formData.ciudad,
      formData.provincia,
      formData.especialidad.length > 0,
      formData.universidad,
    ];
    
    const filledFields = fields.filter(field => field && field !== '').length;
    return Math.round((filledFields / fields.length) * 100);
  }, [formData]);

  const isSaving = updateProfileMutation.isPending;

  return (
    <div className="flex flex-col h-full profile-section" style={{ backgroundColor: '#212121' }}>
      {/* Header */}
      <div className="border-b border-border backdrop-blur-sm p-6" style={{ backgroundColor: '#212121' }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground mb-2">Mi Perfil Profesional</h1>
            <p className="text-muted-foreground">
              Administra tu información profesional y preferencias del sistema
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Indicador de completitud */}
            <div className="text-center">
              <div className="text-lg font-bold text-foreground">{completionPercentage}%</div>
              <div className="text-xs text-muted-foreground">Completo</div>
            </div>
            
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-100 rounded-lg transition-colors"
              >
                <Edit className="w-4 h-4" />
                Editar
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 bg-secondary hover:bg-secondary/90 text-secondary-foreground rounded-lg transition-colors"
                  disabled={isSaving}
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-100 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* Barra de progreso */}
        <div className="mt-4">
          <div className="w-full bg-secondary/20 rounded-full h-2">
            <div 
              className="bg-primary h-2 rounded-full transition-all duration-500"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Información personal */}
          <div className="bg-card/50 border border-border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-6">
              <User className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Información Personal</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Nombre completo *
                </label>
                <input
                  type="text"
                  value={formData.nombre_completo}
                  onChange={(e) => handleInputChange('nombre_completo', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="Juan Pérez García"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Email profesional
                </label>
                <input
                  type="email"
                  value={profile?.email || ''}
                  disabled={true}
                  className="w-full px-3 py-2 bg-secondary/20 border border-secondary/30 rounded-lg text-foreground cursor-not-allowed"
                  placeholder="juan.perez@despacho.com"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  El email no se puede modificar
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Teléfono
                </label>
                <input
                  type="tel"
                  value={formData.telefono}
                  onChange={(e) => handleInputChange('telefono', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="+34 600 123 456"
                />
              </div>
            </div>
          </div>

          {/* Información profesional */}
          <div className="bg-card/50 border border-border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-6">
              <GraduationCap className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Información Profesional</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Matrícula profesional *
                </label>
                <input
                  type="text"
                  value={formData.matricula_profesional}
                  onChange={(e) => handleInputChange('matricula_profesional', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="12345"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Colegio de Abogados
                </label>
                <input
                  type="text"
                  value={formData.colegio_abogados}
                  onChange={(e) => handleInputChange('colegio_abogados', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="Ilustre Colegio de Abogados de Madrid"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Años de experiencia
                </label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  value={formData.anos_experiencia}
                  onChange={(e) => handleInputChange('anos_experiencia', parseInt(e.target.value) || 0)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="5"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Universidad
                </label>
                <input
                  type="text"
                  value={formData.universidad}
                  onChange={(e) => handleInputChange('universidad', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="Universidad Complutense de Madrid"
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-foreground mb-2">
                  Especialidades
                </label>
                <input
                  type="text"
                  value={formData.especialidad.join(', ')}
                  onChange={(e) => handleSpecialtyChange(e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="Derecho Civil, Derecho Laboral, Derecho Penal..."
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Separa las especialidades con comas
                </p>
              </div>
            </div>
          </div>

          {/* Dirección profesional */}
          <div className="bg-card/50 border border-border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-6">
              <MapPin className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Dirección Profesional</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-foreground mb-2">
                  Domicilio profesional
                </label>
                <input
                  type="text"
                  value={formData.domicilio_profesional}
                  onChange={(e) => handleInputChange('domicilio_profesional', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="Calle Alcalá, 123, 2º A"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Código postal
                </label>
                <input
                  type="text"
                  value={formData.codigo_postal}
                  onChange={(e) => handleInputChange('codigo_postal', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="28014"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Ciudad
                </label>
                <input
                  type="text"
                  value={formData.ciudad}
                  onChange={(e) => handleInputChange('ciudad', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="Madrid"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Provincia
                </label>
                <input
                  type="text"
                  value={formData.provincia}
                  onChange={(e) => handleInputChange('provincia', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="Madrid"
                />
              </div>
            </div>
          </div>

          {/* Preferencias del sistema */}
          <div className="bg-card/50 border border-border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-6">
              <Calendar className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Preferencias del Sistema</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Tribunal predeterminado
                </label>
                <input
                  type="text"
                  value={formData.tribunal_predeterminado}
                  onChange={(e) => handleInputChange('tribunal_predeterminado', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="Juzgado de Primera Instancia nº 1 de Madrid"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Formato de demanda preferido
                </label>
                <select
                  value={formData.formato_demanda_preferido}
                  onChange={(e) => handleInputChange('formato_demanda_preferido', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                >
                  <option value="formal">Formal completo</option>
                  <option value="simplificado">Simplificado</option>
                  <option value="completo">Completo detallado</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 