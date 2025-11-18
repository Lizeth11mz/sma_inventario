# admin_sistema/urls.py

from django.urls import path
from . import views

# Namespace para usar: {% url 'admin_sistema:nombre' %}
app_name = 'admin_sistema'

urlpatterns = [

    # ============================
    # 1) LOGIN SEGÚN TIPO DE USUARIO
    # ============================

    # Coincide con {% url 'admin_sistema:login_admin' %}
    path('admin/login/', views.login_admin, name='login_admin'),

    # Coincide con {% url 'admin_sistema:login_warehouse' %}
    path('almacen/login/', views.login_warehouse, name='login_warehouse'),

    # Coincide con {% url 'admin_sistema:login_user' %}
    path('usuario/login/', views.login_user, name='login_user'),

    # ============================
    # 2) GESTIÓN DE USUARIOS (CRUD)
    # ============================

    # Lista de usuarios
    path('usuarios/', views.gestion_usuarios, name='usuarios'),

    # Editar usuario por ID
    path('usuarios/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),

    # Eliminar usuario por ID
    path('usuarios/eliminar/<int:pk>/', views.eliminar_usuario, name='eliminar_usuario'),
]
