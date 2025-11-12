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
    
    # ✅ MEJORA: Se quita 'null=True' y 'blank=True' porque, según tu base de datos, 
    # la ubicación parece ser un campo esencial (Almacén Zona A, etc.). 
    # Si permites nulos aquí, tu vista de movimientos podría fallar si el campo está vacío.
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
    
    # ✅ CORRECCIÓN 1: El campo precio_unitario ya tiene default=0.00, lo que evita errores.
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

    # ✅ CORRECCIÓN 2: Se mantiene el campo para el destino de la salida.
    referencia = models.CharField(
        max_length=150, 
        blank=True, 
        null=True, 
        verbose_name="Destino/Referencia de Salida" # Etiqueta más clara
    ) 

    def __str__(self):
        return f"{self.tipo} de {self.elemento.descripcion} ({self.cantidad}) el {self.fecha_movimiento.strftime('%Y-%m-%d')}"