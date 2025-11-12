# admin_sistema/urls.py

from django.urls import path
from . import views

# Define el nombre del espacio para usarlo en {% url 'admin_sistema:nombre_ruta' %}
app_name = 'admin_sistema'

urlpatterns = [
    # Rutas para la Gestión de Usuarios (Listar y Crear - gestion_usuarios)
    path('usuarios/', views.gestion_usuarios, name='usuarios'),
    
    # RUTA: Edición de usuarios (usando la clave primaria)
    path('usuarios/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    
    # RUTA: Eliminación de usuarios (usando la clave primaria)
    path('usuarios/eliminar/<int:pk>/', views.eliminar_usuario, name='eliminar_usuario'),
]