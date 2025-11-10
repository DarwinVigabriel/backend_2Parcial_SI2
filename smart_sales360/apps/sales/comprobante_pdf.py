"""
CU14: Emitir Comprobante de Venta (PDF)
Módulo para generar comprobantes de venta en PDF usando ReportLab
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os


class ComprobantePDFGenerator:
    """
    Generador de comprobantes de venta en PDF
    Crea un documento profesional con los datos de la venta y detalles
    """
    
    def __init__(self, venta):
        self.venta = venta
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        self._define_custom_styles()
    
    def _define_custom_styles(self):
        """Define estilos personalizados para el PDF"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=6,
            fontName='Helvetica-Bold',
            borderPadding=5,
            backColor=colors.HexColor('#e8f0f8')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4
        ))
    
    def generate(self):
        """Genera el PDF y retorna el buffer"""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Construir elementos del documento
        elements = []
        elements.append(self._create_header())
        elements.append(Spacer(1, 0.2*inch))
        elements.append(self._create_venta_info())
        elements.append(Spacer(1, 0.15*inch))
        elements.append(self._create_cliente_info())
        elements.append(Spacer(1, 0.15*inch))
        elements.append(self._create_detalles_table())
        elements.append(Spacer(1, 0.15*inch))
        elements.append(self._create_totales())
        elements.append(Spacer(1, 0.15*inch))
        elements.append(self._create_pago_info())
        elements.append(Spacer(1, 0.2*inch))
        elements.append(self._create_footer())
        
        # Construir PDF
        doc.build(elements)
        self.buffer.seek(0)
        return self.buffer
    
    def _create_header(self):
        """Crea el encabezado del comprobante"""
        data = [
            [Paragraph('<b>SMART SALES 360</b>', self.styles['CustomTitle'])],
            [Paragraph('Comprobante de Venta', self.styles['SectionTitle'])],
        ]
        
        table = Table(data, colWidths=[7.5*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return table
    
    def _create_venta_info(self):
        """Crea la sección de información de la venta"""
        fecha = self.venta.fecha_venta.strftime('%d/%m/%Y %H:%M')
        
        data = [
            ['Nro. Comprobante:', self.venta.codigo_venta, 'Fecha:', fecha],
            ['Estado:', self.venta.get_estado_display(), 'Tipo Entrega:', self.venta.get_tipo_entrega_display()],
        ]
        
        table = Table(data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f8')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e8f0f8')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return table
    
    def _create_cliente_info(self):
        """Crea la sección de información del cliente"""
        cliente_nombre = self.venta.cliente.nombre_completo if self.venta.cliente else 'Cliente General'
        cliente_email = self.venta.cliente.email if self.venta.cliente else 'N/A'
        vendedor_nombre = self.venta.usuario.nombre if self.venta.usuario else 'N/A'
        
        data = [
            [Paragraph('<b>CLIENTE</b>', self.styles['SectionTitle']), '', 
             Paragraph('<b>VENDEDOR</b>', self.styles['SectionTitle'])],
            [
                f'Nombre: {cliente_nombre}\nEmail: {cliente_email}',
                '',
                f'Vendedor: {vendedor_nombre}\nDirección Entrega: {self.venta.direccion_entrega or "No especificada"}'
            ],
        ]
        
        table = Table(data, colWidths=[2.5*inch, 0.5*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 1), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            ('PADDING', (0, 1), (-1, -1), 8),
        ]))
        
        return table
    
    def _create_detalles_table(self):
        """Crea la tabla de detalles de la venta"""
        data = [
            ['Producto', 'Cant.', 'Precio Unit.', 'Desc. Unit.', 'Subtotal']
        ]
        
        detalles = self.venta.detalles.all()
        for detalle in detalles:
            data.append([
                detalle.producto.nombre if detalle.producto else 'Producto Desconocido',
                str(detalle.cantidad),
                f'${detalle.precio_unitario:.2f}',
                f'${detalle.descuento_unitario:.2f}',
                f'${detalle.subtotal:.2f}',
            ])
        
        table = Table(data, colWidths=[3*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        
        return table
    
    def _create_totales(self):
        """Crea la sección de totales"""
        data = [
            ['', 'Subtotal:', f'${self.venta.subtotal:.2f}'],
            ['', 'Descuento:', f'-${self.venta.descuento:.2f}'],
            ['', 'IVA (19%):', f'${self.venta.iva:.2f}'],
            ['', 'TOTAL:', f'${self.venta.total:.2f}'],
        ]
        
        table = Table(data, colWidths=[4.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 9),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('BACKGROUND', (1, -1), (-1, -1), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (1, -1), (-1, -1), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (1, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return table
    
    def _create_pago_info(self):
        """Crea la sección de información de pago"""
        pagos = self.venta.pagos.all()
        
        if pagos:
            pago = pagos.first()
            info = f'''
            <b>Información de Pago:</b><br/>
            Método: {pago.get_metodo_pago_display()}<br/>
            Estado: {pago.get_estado_display()}<br/>
            Transacción: {pago.numero_transaccion}<br/>
            '''
            
            # Si hay QR, mostrar información
            if pago.qr_codigo:
                info += f'Código QR: {pago.qr_codigo}<br/>'
        else:
            info = '<b>Información de Pago:</b><br/>Pendiente'
        
        return Paragraph(info, self.styles['CustomNormal'])
    
    def _create_footer(self):
        """Crea el pie de página"""
        footer_text = f'''
        <i>Comprobante generado automáticamente por Smart Sales 360<br/>
        Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>
        Este comprobante es válido como documento de venta</i>
        '''
        
        return Paragraph(footer_text, ParagraphStyle(
            name='Footer',
            parent=self.styles['CustomNormal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))


def generar_comprobante_pdf(venta):
    """
    Función helper para generar PDF de comprobante
    
    Args:
        venta: Objeto Venta
    
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    generator = ComprobantePDFGenerator(venta)
    return generator.generate()
