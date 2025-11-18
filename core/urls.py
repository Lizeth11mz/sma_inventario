# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views # Importa las vistas personalizadas

app_name = 'core'

urlpatterns = [
    # ====================================
    # 1. VISTAS PÚBLICAS (ACCESO LIBRE)
    # ====================================
    # RUTA RAÍZ: Muestra la página de inicio (index.html) para todos los visitantes.
    path('', views.index, name='index'), 
    
    # RUTA BIENVENIDA: Para usar después de login o como página informativa.
    path('bienvenido/', views.bienvenido, name='bienvenido'),
    
    # ====================================
    # 2. VISTAS DE AUTENTICACIÓN
    # ====================================
    # LOGIN: Mantiene la vista integrada de Django.
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    
    # LOGOUT: Apunta a la vista personalizada para un cierre limpio.
    path('logout/', views.custom_logout_view, name='logout'),

    # ====================================
    # 3. VISTAS AUTENTICADAS
    # ====================================
    # DASHBOARD: Solo accesible si estás logueado.
    # Nota: Cambiamos el nombre de la ruta a 'dashboard' para ser más claro.
    path('dashboard/', views.home_dashboard, name='dashboard'),
]