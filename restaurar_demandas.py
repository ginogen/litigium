#!/usr/bin/env python3
"""
Script para restaurar las demandas en Supabase desde los archivos SQL exportados
"""

import sys
import os
sys.path.append('.')

from backend.config import supabase
import json
from datetime import datetime

def restaurar_demandas():
    """Restaura las demandas en Supabase."""
    
    print("🔄 Iniciando restauración de demandas...")
    
    # Datos de las demandas del archivo SQL
    demandas = [
        {
            "id": "3dc36f47-8614-4900-8588-547df4f20bc8",
            "sesion_id": None,
            "abogado_id": None,
            "texto_demanda": """TRIBUNAL: Juzgado Nacional de Primera Instancia del Trabajo N° __

EXPEDIENTE: _________

CARATULA: GENTILE, Gino c/ ARCOR S.A s/ Despido

A LA SEÑORÍA:

Yo, __________, abogado, T° __, F° __, CUIT __________, constituyendo domicilio procesal en __________, en representación de Gino Gentile, DNI 35702591, con domicilio en Paraguay 2233, Rosario, según acredito con el poder adjunto, me presento y respetuosamente digo:

HECHOS:

1. Mi mandante, el Sr. Gino Gentile, ha prestado servicios para la demandada, ARCOR S.A, durante 10 años, realizando tareas administrativas.

2. El Sr. Gentile fue despedido sin justa causa.

DERECHO:

El despido sin justa causa se encuentra regulado en los artículos 245 y 232 de la Ley de Contrato de Trabajo (LCT). Según estos artículos, mi mandante tiene derecho a una indemnización por despido sin justa causa, la cual debe ser calculada en base a la mejor remuneración mensual, normal y habitual de los últimos tres meses.

PETITORIO:

En virtud de lo expuesto, solicito:

1. Se declare la procedencia de la demanda y se condene a ARCOR S.A a pagar a mi mandante la indemnización por despido sin justa causa, conforme lo establece el artículo 245 de la LCT.

2. Se condene a ARCOR S.A a pagar las costas del juicio.

OFRECIMIENTO DE PRUEBA:

Ofrezco la siguiente prueba:

1. Documental: Se acompañan recibos de sueldo y telegrama de despido.

2. Testimonial: Se propondrán los testigos en el momento procesal oportuno.

3. Pericial: Se solicitará pericia contable a fin de determinar la mejor remuneración mensual, normal y habitual de los últimos tres meses.

Proveído de conformidad,

SERA JUSTICIA

FIRMA Y DATOS DEL LETRADO:

____________________
Nombre del Letrado
T° __, F° __
CUIT __________
Domicilio Procesal: __________""",
            "version": "1",
            "archivo_docx_url": None,
            "archivo_pdf_url": None,
            "modelo_usado": "gpt-4",
            "casos_consultados": "0",
            "tiempo_generacion": None,
            "created_at": "2025-06-23T14:32:41.813115+00:00",
            "updated_at": "2025-06-23T14:32:41.813115+00:00",
            "session_id": "dab63457-780d-4945-a726-89401b6ee00f",
            "user_id": "ae35cd1f-cf86-40b3-9c0d-eb7b6109f413",
            "tipo_demanda": "Despido",
            "datos_cliente": '{"dni": "35702591", "domicilio": "Paraguay 2233, Rosario", "ocupacion": "tareas administrativas", "nombre_completo": "Gino Gentile"}',
            "hechos_adicionales": "Usuario solicita ayuda con despido. El demandante fue despedido de sus tareas en la empresa ARCOR S.A donde realizaba tareas administrativas durante 10 años",
            "notas_abogado": None,
            "metadatos": '{"cliente": "Gino Gentile", "tipo_demanda": "Despido", "fecha_generacion": "2025-06-23T11:32:41.330557", "casos_consultados": 0, "tiempo_generacion": 28.00832509994507}',
            "archivo_docx": "/var/folders/fv/8pkw66w944d8b17573l09b840000gn/T/tmpgljz7esy.docx",
            "estado": "completado",
            "fecha_generacion": "2025-06-23T11:32:41.330707+00:00"
        },
        {
            "id": "bbc39928-c06f-48ec-b77f-7d420ddd4a20",
            "sesion_id": None,
            "abogado_id": "9e63346c-3686-4f90-885e-1201e6cb8141",
            "texto_demanda": """AL JUZGADO NACIONAL DE PRIMERA INSTANCIA DEL TRABAJO

EXPEDIENTE: GENTILE, GINO C/ ARCOR S.A S/ DESPIDO

GENTILE, GINO, DNI 34.666.777, con domicilio en Paraguay 3344, Rosario, por medio de su abogado constituido, se presenta ante el Juzgado y dice:

I. HECHOS

1. Que mi mandante prestó servicios para la empresa ARCOR S.A, en tareas administrativas durante 10 años, desde el año 2011 hasta la fecha de su despido en 2021.

2. Que durante todo el periodo mencionado, mi mandante no fue registrado debidamente por la empresa, encontrándose en una situación de informalidad laboral.

3. Que el día 1 de octubre de 2021, mi mandante fue despedido sin causa justificada, ni previo aviso, ni indemnización alguna.

II. DERECHO

4. Que la Ley de Contrato de Trabajo (LCT) en su artículo 14 bis establece el derecho a una relación laboral justa y digna, lo cual incluye el derecho a ser registrado debidamente por el empleador.

5. Que el artículo 231 de la LCT establece que en caso de despido sin causa, el trabajador tiene derecho a una indemnización equivalente a un mes de sueldo por cada año de servicio o fracción mayor a tres meses.

6. Que el artículo 45 de la LCT establece que el trabajador tiene derecho a una indemnización por antigüedad equivalente a un mes de sueldo por cada año de servicio o fracción mayor a tres meses.

III. PETITORIO

7. Por todo lo expuesto, solicito:

a) Se declare la existencia de la relación laboral entre mi mandante y la empresa ARCOR S.A durante el periodo 2011-2021.

b) Se condene a la empresa ARCOR S.A a pagar a mi mandante la indemnización por despido sin causa, conforme al artículo 231 de la LCT.

c) Se condene a la empresa ARCOR S.A a pagar a mi mandante la indemnización por antigüedad, conforme al artículo 45 de la LCT.

IV. OFRECIMIENTO DE PRUEBA

8. A los efectos de acreditar los hechos expuestos, ofrezco la siguiente prueba:

a) Testimonial: Se cite a declarar a los compañeros de trabajo de mi mandante.

b) Documental: Se acompañan los recibos de sueldo de mi mandante.

V. FIRMA DEL LETRADO

Por todo lo expuesto, solicito se haga lugar a la demanda.

Firma y sello del letrado""",
            "version": "1",
            "archivo_docx_url": "https://odemisttpuwsgfezotnm.supabase.co/storage/v1/object/public/demandas-generadas/ae35cd1f-cf86-40b3-9c0d-eb7b6109f413/demanda_Gino_Gentile_20250623_121627.docx",
            "archivo_pdf_url": None,
            "modelo_usado": "gpt-4",
            "casos_consultados": "0",
            "tiempo_generacion": None,
            "created_at": "2025-06-23T15:16:29.169194+00:00",
            "updated_at": "2025-06-23T15:16:29.169194+00:00",
            "session_id": "6d29bc76-44fc-4ac0-a43d-ce17f1499cbd",  # ⭐ Esta es la que necesitamos
            "user_id": "ae35cd1f-cf86-40b3-9c0d-eb7b6109f413",
            "tipo_demanda": "Despido_en_Negro",
            "datos_cliente": '{"dni": "34666777", "domicilio": "Paraguay 3344, Rosario", "ocupacion": "tareas administrativas", "nombre_completo": "Gino Gentile"}',
            "hechos_adicionales": "Usuario solicita ayuda con despido. Usuario solicita ayuda con despido. Despedido de ARCOR S.A donde realizaba tareas administrativas durante 10 años, el demándate no estaba registrado y fue despedido sin causa",
            "notas_abogado": None,
            "metadatos": '{"cliente": "Gino Gentile", "tipo_demanda": "Despido_en_Negro", "fecha_generacion": "2025-06-23T12:16:27.482860", "casos_consultados": 0, "tiempo_generacion": 39.45863723754883}',
            "archivo_docx": "/var/folders/fv/8pkw66w944d8b17573l09b840000gn/T/tmp_x4gxlqn.docx",
            "estado": "completado",
            "fecha_generacion": "2025-06-23T12:16:28.798851+00:00"
        }
    ]
    
    # Verificar conexión a Supabase
    try:
        test_response = supabase.table('demandas_generadas').select('id', count='exact').execute()
        print(f"✅ Conexión a Supabase OK. Demandas actuales: {test_response.count}")
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        return
    
    # Insertar demandas
    for i, demanda in enumerate(demandas, 1):
        try:
            print(f"\n🔄 Insertando demanda {i}/{len(demandas)}: session_id={demanda['session_id']}")
            
            # Verificar si ya existe
            existing = supabase.table('demandas_generadas')\
                .select('id')\
                .eq('id', demanda['id'])\
                .execute()
            
            if existing.data:
                print(f"⚠️ Demanda ya existe, actualizando...")
                result = supabase.table('demandas_generadas')\
                    .update(demanda)\
                    .eq('id', demanda['id'])\
                    .execute()
            else:
                print(f"✨ Insertando nueva demanda...")
                result = supabase.table('demandas_generadas')\
                    .insert(demanda)\
                    .execute()
            
            if result.data:
                print(f"✅ Demanda {i} procesada exitosamente")
            else:
                print(f"❌ Error procesando demanda {i}: {result}")
                
        except Exception as e:
            print(f"❌ Error insertando demanda {i}: {e}")
            continue
    
    # Verificar que la demanda objetivo existe
    print(f"\n🔍 Verificando demanda objetivo...")
    target_session = "6d29bc76-44fc-4ac0-a43d-ce17f1499cbd"
    target_user = "ae35cd1f-cf86-40b3-9c0d-eb7b6109f413"
    
    verification = supabase.table('demandas_generadas')\
        .select('id, session_id, user_id, tipo_demanda, estado')\
        .eq('session_id', target_session)\
        .eq('user_id', target_user)\
        .execute()
    
    if verification.data:
        demanda = verification.data[0]
        print(f"✅ Demanda objetivo encontrada:")
        print(f"   - ID: {demanda['id']}")
        print(f"   - Session ID: {demanda['session_id']}")
        print(f"   - User ID: {demanda['user_id']}")
        print(f"   - Tipo: {demanda['tipo_demanda']}")
        print(f"   - Estado: {demanda['estado']}")
        print(f"\n🎉 ¡La restauración fue exitosa! Ahora puedes probar el Canvas.")
    else:
        print(f"❌ No se encontró la demanda objetivo después de la restauración")
    
    print(f"\n✅ Proceso de restauración completado")

if __name__ == "__main__":
    restaurar_demandas() 