# inventario/urls.py

from django.urls import path
from . import views

# app_name es correcto para mantener la consistencia del namespace.
app_name = 'inventario'

urlpatterns = [
    # -------------------------------------------------------------------------
    # --- URLs EXISTENTES (Mantenerlas) ---
    # -------------------------------------------------------------------------
    path('dashboard/', views.inventario_dashboard, name='dashboard'),
    path('entradas/', views.gestion_entradas, name='entradas'),
    path('salidas/', views.gestion_salidas, name='salidas'),
    path('crear_producto/', views.crear_producto, name='crear_producto'), 
    path('gestion_inventario/', views.gestion_inventario, name='gestion_inventario'), 
    path('proveedores/', views.gestion_proveedores, name='proveedores'), 
    path('proveedor/editar/<int:proveedor_id>/', views.editar_proveedor, name='proveedor_editar'),
    path('proveedor/eliminar/<int:proveedor_id>/', views.eliminar_proveedor, name='proveedor_eliminar'),
    
    # -------------------------------------------------------------------------
    # --- URLs de REPORTES (Corregidas y Optimizadas) ---
    # -------------------------------------------------------------------------
    
    # 1. Ruta para mostrar el dashboard de reportes
    path('reportes/', views.reportes_dashboard, name='reportes'), 
    
    # 2. Ruta para generar el reporte de INVENTARIO (XLSX/CVS/PDF)
    path('reportes/generar/', views.generar_reporte, name='generar_reporte'),
    
    # 3. 🆕 RUTA AÑADIDA: Para generar el reporte de MOVIMIENTOS
    path('reportes/movimientos/generar/', views.generar_reporte_movimientos, name='generar_reporte_movimientos'),
    
    # 4. Ruta para descargar el archivo (Usada por ambos generadores)
    # NOTA: filename capturará el nombre completo del archivo.
    path('reportes/descargar/<str:filename>/', views.descargar_reporte, name='descargar_reporte'),
]