# sma_inventario/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Incluir las URLs de las aplicaciones
    path('', include('core.urls')),             # Para Login/Logout
    path('inventario/', include('inventario.urls')), # Para Dashboard, Entradas, Salidas
    path('administracion/', include('admin_sistema.urls')), # Para Usuarios, Proveedores, Reportes
]