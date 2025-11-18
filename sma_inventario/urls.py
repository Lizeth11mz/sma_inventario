# sma_inventario/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. RUTA DE ADMINISTRACIÓN DE DJANGO (Admin Site)
    path('admin/', admin.site.urls),
    
    # 2. RUTA PRINCIPAL (CORE)
    # Incluye las URLs de la aplicación 'core' en la raíz del proyecto.
    # Maneja index, login/logout, bienvenido, y el dashboard principal.
    path('', include('core.urls')), 
    
    # 3. RUTA INVENTARIO
    # Incluye las URLs de la aplicación 'inventario' con el prefijo '/inventario/'.
    # Nota: No se requiere namespace aquí a menos que tengas conflictos de nombres.
    path('inventario/', include('inventario.urls')), 
    
    # 4. RUTA ADMINISTRACIÓN DEL SISTEMA
    # FIX IMPORTANTE: Incluimos las URLs de la aplicación 'admin_sistema' 
    # y DEFINIMOS EL NAMESPACE para que funcionen las llamadas tipo 'admin_sistema:login_...'
    path('administracion/', include('admin_sistema.urls', namespace='admin_sistema')), 
]