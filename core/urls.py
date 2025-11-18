# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views   # Importa tus vistas personalizadas

app_name = 'core'

urlpatterns = [
    # ====================================
    # 1. VISTAS PÚBLICAS (ACCESO LIBRE)
    # ====================================
    
    # Página principal (index.html)
    path('', views.index, name='index'),

    # Página intermedia de bienvenida
    path('bienvenido/', views.bienvenido, name='bienvenido'),

    # ====================================
    # 2. AUTENTICACIÓN DEL SISTEMA
    # ====================================

    # Login usando plantilla core/login.html
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='core/login.html'),
        name='login'
    ),

    # Logout usando tu vista personalizada
    path('logout/', views.custom_logout_view, name='logout'),

    # ====================================
    # 3. VISTAS PROTEGIDAS (requieren login)
    # ====================================

    # Dashboard general del sistema
    path('dashboard/', views.home_dashboard, name='dashboard'),
]
