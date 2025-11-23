# sma_inventario/urls.py
from django.contrib import admin
from django.urls import path, include

# Importaciones necesarias para servir archivos MEDIA en DEBUG=True
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. URLs de la aplicación core (Login/Logout)
    path('', include('core.urls')),
    
    # 2. URLs de la aplicación inventario: (Manteniendo tu namespace)
    path('inventario/', include('inventario.urls', namespace='inventario')),
    
    # 3. URLs de la aplicación admin_sistema: (Manteniendo tu namespace)
    path('administracion/', include('admin_sistema.urls', namespace='admin_sistema')),
]

# 💾 Configuración para servir archivos MEDIA en modo Desarrollo
# ESTA ES LA CORRECCIÓN CRUCIAL:
# Solo agrega la configuración de MEDIA si DEBUG está activado en settings.py
if settings.DEBUG:
    # Esta línea mapea la URL '/media/' a la carpeta definida en MEDIA_ROOT
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)