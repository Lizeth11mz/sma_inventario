# sma_inventario/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. RUTA DE ADMINISTRACIÓN DE DJANGO (Admin Site)
    path('admin/', admin.site.urls),
    
    # 2. RUTA PRINCIPAL (CORE)
    # Incluye las URLs de la aplicación 'core' en la raíz del proyecto.
    # Aquí se manejan el index, login/logout, y el dashboard principal.
    path('', include('core.urls')), 
    
    # 3. RUTA INVENTARIO
    # Incluye las URLs de la aplicación 'inventario' con el prefijo '/inventario/'.
    path('inventario/', include('inventario.urls')), 
    
    # 4. RUTA ADMINISTRACIÓN DEL SISTEMA
    # Incluye las URLs de la aplicación 'admin_sistema' con el prefijo '/administracion/'.
    path('administracion/', include('admin_sistema.urls')), 
]