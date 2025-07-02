import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '@/utils';
import { User, Mail, Phone, MapPin, GraduationCap, Building, Save, Edit, FileText, CreditCard } from 'lucide-react';

export function ProfileSection() {
  const { profile, updateProfile, refreshProfile } = useAuth();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    nombre_completo: '',
    matricula_profesional: '',
    colegio_abogados: '',
    telefono: '',
    domicilio_profesional: '',
    tomo: '',
    folio: '',
    condicion_fiscal: '',
    cuit: '',
    legajo: '',
    nombre_estudio: '',
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
        tomo: profile.tomo || '',
        folio: profile.folio || '',
        condicion_fiscal: profile.condicion_fiscal || '',
        cuit: profile.cuit || '',
        legajo: profile.legajo || '',
        nombre_estudio: profile.nombre_estudio || '',
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
        tomo: profile.tomo || '',
        folio: profile.folio || '',
        condicion_fiscal: profile.condicion_fiscal || '',
        cuit: profile.cuit || '',
        legajo: profile.legajo || '',
        nombre_estudio: profile.nombre_estudio || '',
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
      formData.tomo,
      formData.folio,
      formData.condicion_fiscal,
      formData.cuit,
      formData.legajo,
      formData.nombre_estudio,
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
              Administra tu información profesional y datos del estudio jurídico
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
          {/* Información personal y de contacto */}
          <div className="bg-card/50 border border-border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-6">
              <User className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Información Personal y Contacto</h2>
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
                  placeholder="+54 11 1234-5678"
                />
              </div>
              
              <div>
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
                  placeholder="Av. Corrientes 1234, CABA"
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
                  placeholder="Colegio de Abogados de la Ciudad de Buenos Aires"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Tomo
                </label>
                <input
                  type="text"
                  value={formData.tomo}
                  onChange={(e) => handleInputChange('tomo', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="123"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Folio
                </label>
                <input
                  type="text"
                  value={formData.folio}
                  onChange={(e) => handleInputChange('folio', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="456"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Legajo
                </label>
                <input
                  type="text"
                  value={formData.legajo}
                  onChange={(e) => handleInputChange('legajo', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="L-789"
                />
              </div>
            </div>
          </div>

          {/* Información fiscal y estudio */}
          <div className="bg-card/50 border border-border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-6">
              <Building className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Información Fiscal y Estudio</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Condición Fiscal
                </label>
                <select
                  value={formData.condicion_fiscal}
                  onChange={(e) => handleInputChange('condicion_fiscal', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                >
                  <option value="">Seleccionar condición fiscal</option>
                  <option value="Responsable Inscripto">Responsable Inscripto</option>
                  <option value="Monotributista">Monotributista</option>
                  <option value="Exento">Exento</option>
                  <option value="No Responsable">No Responsable</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  CUIT
                </label>
                <input
                  type="text"
                  value={formData.cuit}
                  onChange={(e) => handleInputChange('cuit', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="20-12345678-9"
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-foreground mb-2">
                  Nombre del Estudio
                </label>
                <input
                  type="text"
                  value={formData.nombre_estudio}
                  onChange={(e) => handleInputChange('nombre_estudio', e.target.value)}
                  disabled={!isEditing}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg text-foreground transition-colors",
                    isEditing 
                      ? "bg-background border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      : "bg-secondary/20 border-secondary/30 cursor-not-allowed"
                  )}
                  placeholder="Estudio Jurídico Pérez & Asociados"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 