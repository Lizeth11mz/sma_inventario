# inventario/models.py
from django.db import models
from django.contrib.auth.models import User 

# --- Modelos de Clasificación y Proveedor ---

class ClaseInventario(models.Model):
    """Clasificación o Rubro de los elementos (Ej. Material de Limpieza)."""
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Proveedor(models.Model):
    """Información de los proveedores."""
    nombre = models.CharField(max_length=150)
    rfc = models.CharField(max_length=20, unique=True, blank=True, null=True)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    
    # Dirección y Giro
    direccion = models.CharField(
        max_length=250, 
        blank=True, 
        null=True, 
        verbose_name="Dirección Completa"
    ) 
    giro = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="Giro del Proveedor"
    ) 
    activo = models.BooleanField(default=True, verbose_name="Estado Activo")

    def __str__(self):
        return self.nombre

# --- Modelo Principal de Inventario ---
    
class ElementoInventario(models.Model):
    """El maestro de elementos (productos) que se manejan en el sistema."""
    clase = models.ForeignKey(ClaseInventario, on_delete=models.PROTECT)
    descripcion = models.CharField(max_length=250, unique=True)
    unidad = models.CharField(max_length=10)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Se recomienda mantener NOT NULL si es un campo esencial
    ubicacion = models.CharField(max_length=100) 
    
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.descripcion

# --- Modelo de Movimientos ---
    
class MovimientoInventario(models.Model):
    """Registro de Entradas y Salidas."""
    TIPO_MOVIMIENTO_CHOICES = (
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    )
    elemento = models.ForeignKey(ElementoInventario, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Costo/Precio Unitario del Movimiento"
    )
    
    # Vincula al proveedor directamente (solo para Entradas)
    proveedor = models.ForeignKey(
        Proveedor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Proveedor de Entrada"
    )
    
    # Para registrar el documento de la entrada/salida
    folio_documento = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="Folio/Factura"
    )

    # Campo para el destino de la salida.
    referencia = models.CharField(
        max_length=150, 
        blank=True, 
        null=True, 
        verbose_name="Destino/Referencia de Salida"
    ) 

    # 🚀 MÉTODO PARA PERSONALIZAR EL RESPONSABLE 🚀
    def get_responsable_display(self):
        """
        Devuelve el nombre personalizado (ej. 'Lizeth') para usuarios específicos, 
        o el nombre completo del usuario si no hay un mapeo.
        """
        # Define el mapeo de nombres de usuario a nombres de visualización
        nombre_mapeado = {
            'lmartinez': 'Lizeth',
            # Puedes añadir más usuarios aquí:
            'lzamora': 'Juan',
        }
        
        username = self.responsable.username
        
        # 1. Verificar si el username está en el mapeo
        if username in nombre_mapeado:
            return nombre_mapeado[username]
            
        # 2. Si no está en el mapeo, intentar devolver el nombre completo (First Name + Last Name)
        full_name = self.responsable.get_full_name()
        if full_name:
            return full_name
            
        # 3. Si no hay nombre completo, devolver el username
        return username

    def __str__(self):
        return f"{self.tipo} de {self.elemento.descripcion} ({self.cantidad}) el {self.fecha_movimiento.strftime('%Y-%m-%d')}"