"""
Enhanced Document Processor with Rich Format Preservation
Procesador de documentos mejorado que preserva formato completo
"""

import os
import tempfile
import mimetypes
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
import uuid

from docx import Document
from docx.shared import RGBColor
from docx.enum.dml import MSO_COLOR_TYPE
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
import PyPDF2

class RichFormatDocumentProcessor:
    """Procesador de documentos que preserva formato completo."""
    
    def __init__(self):
        """Inicializa el procesador con capacidades de formato rico."""
        pass
    
    def extract_rich_content_from_file(self, file_path: str, mime_type: str = None) -> Tuple[Dict, Dict]:
        """
        Extrae contenido con formato rico de diferentes tipos de archivo.
        
        Returns:
            Tuple[Dict, Dict]: (rich_content, metadata)
            - rich_content: Estructura con texto y formato
            - metadata: Información sobre la extracción
        """
        try:
            if mime_type is None:
                mime_type, _ = mimetypes.guess_type(file_path)
            
            rich_content = {"type": "document", "blocks": []}
            metadata = {"extraction_method": "", "format_preserved": True}
            
            if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                # DOCX con formato rico
                rich_content, metadata = self._extract_rich_from_docx(file_path)
            elif mime_type == "application/pdf":
                # PDF básico (texto plano)
                rich_content, metadata = self._extract_from_pdf_basic(file_path)
            elif mime_type == "text/plain":
                # TXT básico
                rich_content, metadata = self._extract_from_txt_basic(file_path)
            else:
                raise Exception(f"Tipo de archivo no soportado para formato rico: {mime_type}")
            
            return rich_content, metadata
            
        except Exception as e:
            raise Exception(f"Error extrayendo contenido rico del archivo: {e}")
    
    def _extract_rich_from_docx(self, file_path: str) -> Tuple[Dict, Dict]:
        """Extrae contenido rico de archivo DOCX preservando formato."""
        try:
            doc = Document(file_path)
            rich_content = {
                "type": "document",
                "blocks": [],
                "styles": {},
                "metadata": {}
            }
            
            # Extraer cada elemento del documento
            for element in self._iter_block_items(doc):
                if isinstance(element, Paragraph):
                    para_block = self._extract_paragraph_with_format(element)
                    if para_block["content"] or para_block["runs"]:  # Solo si tiene contenido
                        rich_content["blocks"].append(para_block)
                elif isinstance(element, Table):
                    table_block = self._extract_table_with_format(element)
                    rich_content["blocks"].append(table_block)
            
            metadata = {
                "extraction_method": "python-docx-rich",
                "format_preserved": True,
                "total_blocks": len(rich_content["blocks"]),
                "has_tables": any(b["type"] == "table" for b in rich_content["blocks"]),
                "has_formatting": any(
                    any(r.get("bold") or r.get("italic") or r.get("underline") 
                        for r in b.get("runs", [])) 
                    for b in rich_content["blocks"] if b["type"] == "paragraph"
                )
            }
            
            return rich_content, metadata
            
        except Exception as e:
            raise Exception(f"Error procesando DOCX con formato rico: {e}")
    
    def _iter_block_items(self, parent):
        """
        Itera sobre párrafos y tablas en orden del documento.
        Similar al código encontrado en el research web.
        """
        from docx.document import Document as _Document
        
        if isinstance(parent, _Document):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            raise ValueError("Tipo de parent no soportado")
            
        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)
    
    def _extract_paragraph_with_format(self, paragraph) -> Dict:
        """Extrae un párrafo con todo su formato."""
        para_data = {
            "type": "paragraph",
            "content": paragraph.text,
            "style": paragraph.style.name if paragraph.style else "Normal",
            "alignment": str(paragraph.alignment) if paragraph.alignment else None,
            "runs": [],
            "formatting": {
                "space_before": paragraph.paragraph_format.space_before.pt if paragraph.paragraph_format.space_before else None,
                "space_after": paragraph.paragraph_format.space_after.pt if paragraph.paragraph_format.space_after else None,
                "line_spacing": paragraph.paragraph_format.line_spacing if paragraph.paragraph_format.line_spacing else None,
                "first_line_indent": paragraph.paragraph_format.first_line_indent.pt if paragraph.paragraph_format.first_line_indent else None,
                "left_indent": paragraph.paragraph_format.left_indent.pt if paragraph.paragraph_format.left_indent else None,
                "right_indent": paragraph.paragraph_format.right_indent.pt if paragraph.paragraph_format.right_indent else None
            }
        }
        
        # Extraer cada run con su formato específico
        for run in paragraph.runs:
            run_data = self._extract_run_with_format(run)
            if run_data["text"]:  # Solo agregar runs con texto
                para_data["runs"].append(run_data)
        
        return para_data
    
    def _extract_run_with_format(self, run) -> Dict:
        """Extrae un run con todo su formato de carácter."""
        font = run.font
        
        # Determinar color de forma segura
        font_color = None
        try:
            if font.color and font.color.type == MSO_COLOR_TYPE.RGB and font.color.rgb:
                rgb = font.color.rgb
                font_color = f"#{rgb.r:02x}{rgb.g:02x}{rgb.b:02x}"
            elif font.color and font.color.type == MSO_COLOR_TYPE.THEME:
                font_color = f"theme:{font.color.theme_color}"
        except:
            font_color = None
        
        run_data = {
            "text": run.text,
            "bold": font.bold,
            "italic": font.italic,
            "underline": font.underline,
            "font_name": font.name,
            "font_size": font.size.pt if font.size else None,
            "font_color": font_color,
            "strikethrough": font.strike,
            "subscript": font.subscript,
            "superscript": font.superscript,
            "all_caps": font.all_caps,
            "small_caps": font.small_caps
        }
        
        return run_data
    
    def _extract_table_with_format(self, table) -> Dict:
        """Extrae una tabla con formato completo."""
        table_data = {
            "type": "table",
            "style": table.style.name if table.style else "Table Normal",
            "rows": []
        }
        
        for row in table.rows:
            row_data = {"cells": []}
            
            for cell in row.cells:
                cell_data = {
                    "content": [],
                    "vertical_alignment": str(cell.vertical_alignment) if cell.vertical_alignment else None
                }
                
                # Procesar contenido de la celda (párrafos y tablas anidadas)
                for element in self._iter_block_items(cell):
                    if isinstance(element, Paragraph):
                        para_block = self._extract_paragraph_with_format(element)
                        if para_block["content"] or para_block["runs"]:
                            cell_data["content"].append(para_block)
                    elif isinstance(element, Table):
                        nested_table = self._extract_table_with_format(element)
                        cell_data["content"].append(nested_table)
                
                row_data["cells"].append(cell_data)
            
            table_data["rows"].append(row_data)
        
        return table_data
    
    def _extract_from_pdf_basic(self, file_path: str) -> Tuple[Dict, Dict]:
        """Extrae texto básico de PDF (sin formato)."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pages_count = len(pdf_reader.pages)
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # Convertir a formato de bloque simple
            rich_content = {
                "type": "document",
                "blocks": [
                    {
                        "type": "paragraph",
                        "content": text.strip(),
                        "style": "Normal",
                        "runs": [{"text": text.strip(), "bold": None, "italic": None}]
                    }
                ]
            }
            
            metadata = {
                "extraction_method": "PyPDF2-basic",
                "format_preserved": False,
                "pages_count": pages_count,
                "warning": "PDF extraído como texto plano, sin formato"
            }
            
            return rich_content, metadata
            
        except Exception as e:
            raise Exception(f"Error procesando PDF básico: {e}")
    
    def _extract_from_txt_basic(self, file_path: str) -> Tuple[Dict, Dict]:
        """Extrae texto de TXT."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            rich_content = {
                "type": "document",
                "blocks": [
                    {
                        "type": "paragraph",
                        "content": text.strip(),
                        "style": "Normal",
                        "runs": [{"text": text.strip(), "bold": None, "italic": None}]
                    }
                ]
            }
            
            metadata = {
                "extraction_method": "direct-read-txt",
                "format_preserved": False,
                "encoding": "utf-8"
            }
            
            return rich_content, metadata
            
        except Exception as e:
            raise Exception(f"Error procesando TXT: {e}")
    
    def serialize_rich_content(self, rich_content: Dict) -> str:
        """Serializa el contenido rico a JSON para almacenamiento."""
        return json.dumps(rich_content, ensure_ascii=False, indent=2)
    
    def rich_content_to_html(self, rich_content: Dict) -> str:
        """Convierte contenido rico a HTML para visualización."""
        html_parts = ["<div class='rich-document'>"]
        
        for block in rich_content.get("blocks", []):
            if block["type"] == "paragraph":
                html_parts.append(self._paragraph_to_html(block))
            elif block["type"] == "table":
                html_parts.append(self._table_to_html(block))
        
        html_parts.append("</div>")
        return "\n".join(html_parts)
    
    def _paragraph_to_html(self, para_block: Dict) -> str:
        """Convierte un párrafo a HTML preservando formato."""
        style_name = para_block.get("style", "Normal")
        
        # Determinar tag HTML basado en estilo
        if "Heading" in style_name:
            level = style_name.split()[-1] if style_name.split()[-1].isdigit() else "1"
            tag = f"h{level}"
        else:
            tag = "p"
        
        html = f"<{tag}>"
        
        # Procesar runs con formato
        for run in para_block.get("runs", []):
            html += self._run_to_html(run)
        
        html += f"</{tag}>"
        return html
    
    def _run_to_html(self, run_data: Dict) -> str:
        """Convierte un run a HTML con formato."""
        text = run_data.get("text", "")
        
        # Aplicar formatos de texto
        if run_data.get("bold"):
            text = f"<strong>{text}</strong>"
        
        if run_data.get("italic"):
            text = f"<em>{text}</em>"
        
        if run_data.get("underline"):
            text = f"<u>{text}</u>"
        
        if run_data.get("strikethrough"):
            text = f"<s>{text}</s>"
        
        # Aplicar estilos CSS si hay color o tamaño de fuente
        styles = []
        if run_data.get("font_color"):
            styles.append(f"color: {run_data['font_color']}")
        
        if run_data.get("font_size"):
            styles.append(f"font-size: {run_data['font_size']}pt")
        
        if run_data.get("font_name"):
            styles.append(f"font-family: '{run_data['font_name']}'")
        
        if styles:
            style_attr = "; ".join(styles)
            text = f"<span style='{style_attr}'>{text}</span>"
        
        return text
    
    def _table_to_html(self, table_block: Dict) -> str:
        """Convierte una tabla a HTML preservando formato."""
        html = ["<table class='formatted-table' border='1' style='border-collapse: collapse;'>"]
        
        for row in table_block.get("rows", []):
            html.append("<tr>")
            
            for cell in row.get("cells", []):
                html.append("<td>")
                
                # Procesar contenido de la celda
                for content_block in cell.get("content", []):
                    if content_block["type"] == "paragraph":
                        html.append(self._paragraph_to_html(content_block))
                    elif content_block["type"] == "table":
                        html.append(self._table_to_html(content_block))
                
                html.append("</td>")
            
            html.append("</tr>")
        
        html.append("</table>")
        return "\n".join(html)


# Global instance
rich_format_processor = RichFormatDocumentProcessor() 