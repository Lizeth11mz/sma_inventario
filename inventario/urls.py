# inventario/urls.py

from django.urls import path
from . import views

# Define el nombre del espacio para usarlo en {% url 'inventario:nombre_ruta' %}
app_name = 'inventario'

urlpatterns = [
    # ---------------------------------------------------
    # RUTAS PRINCIPALES
    # ---------------------------------------------------
    path('dashboard/', views.inventario_dashboard, name='dashboard'),
    
    # Rutas de Movimientos
    path('entradas/', views.gestion_entradas, name='entradas'),
    path('salidas/', views.gestion_salidas, name='salidas'),
    
    # Rutas para el CRUD de Elementos (Productos)
    # 💡 Se ha unificado la ruta del modal (era 'crear-producto/')
    path('crear_producto/', views.crear_producto, name='crear_producto'), 
    
    # 💡 Nota: gestion_inventario está en views.py, pero redirige al dashboard.
    path('gestion_inventario/', views.gestion_inventario, name='gestion_inventario'), 
    
    # ---------------------------------------------------
    # RUTAS DE PROVEEDORES
    # ---------------------------------------------------
    path('proveedores/', views.gestion_proveedores, name='proveedores'), 
    
    # Editar proveedor
    path('proveedor/editar/<int:proveedor_id>/', views.editar_proveedor, name='proveedor_editar'),
    
    # Eliminar proveedor (usada con POST)
    path('proveedor/eliminar/<int:proveedor_id>/', views.eliminar_proveedor, name='proveedor_eliminar'),
    
    # ---------------------------------------------------
    # RUTAS DE REPORTES
    # ---------------------------------------------------
    path('reportes/', views.gestion_reportes, name='reportes'), 
]