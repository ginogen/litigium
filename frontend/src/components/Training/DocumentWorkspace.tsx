import React, { useState, useEffect } from 'react';
import { cn } from '@/utils';
import { 
  FileText, 
  MessageSquare,
  BookTemplate,
  Split,
  Maximize2,
  Minimize2,
  Settings,
  Filter,
  Layout
} from 'lucide-react';
import { DocumentLibrary } from './DocumentLibrary';
import { DocumentViewer } from './DocumentViewer';
import { AnnotationPanel } from './AnnotationPanel';
import { AnnotationForm } from './AnnotationForm';
import { AnnotationTemplates } from './AnnotationTemplates';

interface Document {
  id: string;
  nombre_archivo: string;
  archivo_url: string;
  tipo_mime: string;
  tipo_demanda: string;
  estado_procesamiento: string;
  vectorizado: boolean;
  created_at: string;
  processed_at?: string;
  categoria?: {
    nombre: string;
    color: string;
    icon: string;
  };
  tamaño_bytes?: number;
  error_procesamiento?: string;
  total_anotaciones?: number;
}

interface Annotation {
  id: string;
  posicion_inicio: number;
  posicion_fin: number;
  contenido_seleccionado: string;
  contenido_anotacion: string;
  tipo: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  etiquetas?: string[];
  prioridad?: number;
  created_at: string;
  author?: string;
}

interface Template {
  id?: string;
  nombre: string;
  tipo: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  contenido: string;
  etiquetas: string[];
  prioridad_sugerida?: number;
  is_default?: boolean;
}

interface DocumentWorkspaceProps {
  selectedCategoryId?: string;
}

export function DocumentWorkspace({ selectedCategoryId }: DocumentWorkspaceProps) {
  const [layout, setLayout] = useState<'split' | 'full-document' | 'full-library'>('split');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [selectedAnnotation, setSelectedAnnotation] = useState<Annotation | null>(null);
  const [showAnnotationForm, setShowAnnotationForm] = useState(false);
  const [editingAnnotation, setEditingAnnotation] = useState<Annotation | null>(null);
  const [selectedText, setSelectedText] = useState<string>('');
  const [templates, setTemplates] = useState<Template[]>([]);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showAnnotationPanel, setShowAnnotationPanel] = useState(true);

  // Datos mock para desarrollo
  const mockDocuments: Document[] = [
    {
      id: '1',
      nombre_archivo: 'Caso_Despido_Injustificado.pdf',
      archivo_url: 'https://ejemplo.com/doc1.pdf',
      tipo_mime: 'application/pdf',
      tipo_demanda: 'Despido Injustificado',
      estado_procesamiento: 'completado',
      vectorizado: true,
      created_at: '2024-01-15T10:30:00Z',
      processed_at: '2024-01-15T10:35:00Z',
      categoria: {
        nombre: 'Derecho Laboral',
        color: '#3b82f6',
        icon: '⚖️'
      },
      tamaño_bytes: 2048576,
      total_anotaciones: 5
    },
    {
      id: '2',
      nombre_archivo: 'Demanda_Accidente_Laboral.docx',
      archivo_url: 'https://ejemplo.com/doc2.docx',
      tipo_mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      tipo_demanda: 'Accidente Laboral',
      estado_procesamiento: 'completado',
      vectorizado: true,
      created_at: '2024-01-16T14:20:00Z',
      categoria: {
        nombre: 'Derecho Laboral',
        color: '#3b82f6',
        icon: '⚖️'
      },
      tamaño_bytes: 1536000,
      total_anotaciones: 3
    }
  ];

  const mockAnnotations: Annotation[] = [
    {
      id: '1',
      posicion_inicio: 100,
      posicion_fin: 200,
      contenido_seleccionado: 'El trabajador fue despedido sin causa justificada',
      contenido_anotacion: 'Este es un caso típico de despido sin causa. Se debe analizar si se cumplieron los requisitos del art. 245 LCT.',
      tipo: 'problema',
      etiquetas: ['despido', 'LCT', 'art-245'],
      prioridad: 8,
      created_at: '2024-01-15T11:00:00Z',
      author: 'Dr. García'
    },
    {
      id: '2',
      posicion_inicio: 300,
      posicion_fin: 400,
      contenido_seleccionado: 'indemnización por despido',
      contenido_anotacion: 'Verificar cálculo de antigüedad y aplicar precedente "Fernández c/ Empresa XYZ" que establece criterios similares.',
      tipo: 'precedente',
      etiquetas: ['indemnización', 'precedente', 'cálculo'],
      prioridad: 7,
      created_at: '2024-01-15T11:15:00Z',
      author: 'Dr. García'
    }
  ];

  useEffect(() => {
    // Cargar anotaciones del documento seleccionado
    if (selectedDocument) {
      setAnnotations(mockAnnotations);
    } else {
      setAnnotations([]);
    }
  }, [selectedDocument]);

  const handleDocumentSelect = (document: Document) => {
    setSelectedDocument(document);
    if (layout === 'full-library') {
      setLayout('split');
    }
  };

  const handleAnnotationCreate = (annotation: Partial<Annotation>) => {
    const newAnnotation: Annotation = {
      ...annotation,
      id: Date.now().toString(),
      created_at: new Date().toISOString(),
      author: 'Usuario Actual'
    } as Annotation;

    setAnnotations(prev => [...prev, newAnnotation]);
    setShowAnnotationForm(false);
    setSelectedText('');
  };

  const handleAnnotationUpdate = (annotation: Annotation) => {
    setAnnotations(prev => prev.map(a => a.id === annotation.id ? annotation : a));
    setShowAnnotationForm(false);
    setEditingAnnotation(null);
  };

  const handleAnnotationDelete = (annotationId: string) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta anotación?')) {
      setAnnotations(prev => prev.filter(a => a.id !== annotationId));
      if (selectedAnnotation?.id === annotationId) {
        setSelectedAnnotation(null);
      }
    }
  };

  const handleTemplateUse = (template: Template) => {
    setEditingAnnotation({
      id: '',
      posicion_inicio: 0,
      posicion_fin: 0,
      contenido_seleccionado: selectedText,
      contenido_anotacion: template.contenido,
      tipo: template.tipo,
      etiquetas: template.etiquetas,
      prioridad: template.prioridad_sugerida || 5,
      created_at: new Date().toISOString(),
      author: 'Usuario Actual'
    });
    setShowAnnotationForm(true);
    setShowTemplates(false);
  };

  const getLayoutIcon = () => {
    switch (layout) {
      case 'split':
        return <Split className="w-4 h-4" />;
      case 'full-document':
        return <Maximize2 className="w-4 h-4" />;
      case 'full-library':
        return <FileText className="w-4 h-4" />;
      default:
        return <Layout className="w-4 h-4" />;
    }
  };

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <FileText className="w-6 h-6 text-primary" />
          <h2 className="text-xl font-semibold text-foreground">Documentos y Anotaciones</h2>
        </div>

        <div className="flex items-center gap-2">
          {/* Control de layout */}
          <div className="flex items-center border border-border rounded-lg p-1">
            <button
              onClick={() => setLayout('full-library')}
              className={cn(
                "p-2 rounded transition-colors",
                layout === 'full-library' 
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-background"
              )}
              title="Solo biblioteca"
            >
              <FileText className="w-4 h-4" />
            </button>
            <button
              onClick={() => setLayout('split')}
              className={cn(
                "p-2 rounded transition-colors",
                layout === 'split'
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-background"
              )}
              title="Vista dividida"
            >
              <Split className="w-4 h-4" />
            </button>
            <button
              onClick={() => setLayout('full-document')}
              className={cn(
                "p-2 rounded transition-colors",
                layout === 'full-document'
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-background"
              )}
              title="Documento completo"
              disabled={!selectedDocument}
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>

          {/* Panel de anotaciones */}
          {selectedDocument && layout !== 'full-library' && (
            <button
              onClick={() => setShowAnnotationPanel(!showAnnotationPanel)}
              className={cn(
                "p-2 border border-border rounded-lg transition-colors",
                showAnnotationPanel
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-background"
              )}
              title="Alternar panel de anotaciones"
            >
              <MessageSquare className="w-4 h-4" />
            </button>
          )}

          {/* Plantillas */}
          <button
            onClick={() => setShowTemplates(!showTemplates)}
            className={cn(
              "p-2 border border-border rounded-lg transition-colors",
              showTemplates
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-background"
            )}
            title="Plantillas de anotaciones"
          >
            <BookTemplate className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="flex-1 flex overflow-hidden">
        {/* Biblioteca de documentos */}
        {(layout === 'full-library' || layout === 'split') && (
          <div className={cn(
            "border-r border-border bg-background",
            layout === 'full-library' ? "flex-1" : "w-80 flex-shrink-0"
          )}>
            <DocumentLibrary
              onDocumentSelect={handleDocumentSelect}
              selectedCategoryId={selectedCategoryId}
            />
          </div>
        )}

        {/* Visor de documentos */}
        {selectedDocument && (layout === 'full-document' || layout === 'split') && (
          <div className="flex-1 flex overflow-hidden">
            <div className="flex-1">
              <DocumentViewer
                document={selectedDocument}
                annotations={annotations}
                onClose={() => {
                  if (layout === 'full-document') {
                    setLayout('split');
                  } else {
                    setSelectedDocument(null);
                  }
                }}
                onAnnotationCreate={(annotation) => {
                  setEditingAnnotation(annotation as Annotation);
                  setSelectedText(annotation.contenido_seleccionado || '');
                  setShowAnnotationForm(true);
                }}
                onAnnotationSelect={setSelectedAnnotation}
                showAnnotations={showAnnotationPanel}
              />
            </div>

            {/* Panel de anotaciones */}
            {showAnnotationPanel && (
              <AnnotationPanel
                annotations={annotations}
                selectedAnnotationId={selectedAnnotation?.id}
                onAnnotationSelect={setSelectedAnnotation}
                onAnnotationEdit={(annotation) => {
                  setEditingAnnotation(annotation);
                  setShowAnnotationForm(true);
                }}
                onAnnotationDelete={handleAnnotationDelete}
              />
            )}
          </div>
        )}

        {/* Mensaje de estado cuando no hay documento seleccionado */}
        {!selectedDocument && layout !== 'full-library' && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <FileText className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">
                Selecciona un documento
              </h3>
              <p className="text-sm text-muted-foreground">
                Elige un documento de la biblioteca para ver y anotar su contenido
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Panel de plantillas */}
      {showTemplates && (
        <div className="absolute inset-0 z-40 bg-black/50 backdrop-blur-sm flex items-center justify-center">
          <div className="bg-background border border-border rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-border flex items-center justify-between">
              <h3 className="text-lg font-semibold text-foreground">Plantillas de Anotaciones</h3>
              <button
                onClick={() => setShowTemplates(false)}
                className="p-2 text-muted-foreground hover:text-foreground hover:bg-background rounded-lg transition-colors"
              >
                <Minimize2 className="w-4 h-4" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-80px)]">
              <AnnotationTemplates
                templates={templates}
                onTemplateCreate={(template) => {
                  setTemplates(prev => [...prev, { ...template, id: Date.now().toString() }]);
                }}
                onTemplateUpdate={(template) => {
                  setTemplates(prev => prev.map(t => t.id === template.id ? template : t));
                }}
                onTemplateDelete={(templateId) => {
                  setTemplates(prev => prev.filter(t => t.id !== templateId));
                }}
                onTemplateUse={handleTemplateUse}
              />
            </div>
          </div>
        </div>
      )}

      {/* Formulario de anotaciones */}
      <AnnotationForm
        annotation={editingAnnotation}
        selectedText={selectedText}
        isOpen={showAnnotationForm}
        onClose={() => {
          setShowAnnotationForm(false);
          setEditingAnnotation(null);
          setSelectedText('');
        }}
        onSave={editingAnnotation?.id ? handleAnnotationUpdate : handleAnnotationCreate}
        templates={templates}
      />
    </div>
  );
} 