# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views # Importa la vista personalizada 'custom_logout_view'

app_name = 'core'

urlpatterns = [
    # 1. RUTA RAÍZ (HOME)
    path('', views.home_dashboard, name='home'), 
    
    # 2. LOGIN: Mantiene la vista integrada de Django
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    
    # 3. LOGOUT: 🟢 CORREGIDO: Apunta a la vista personalizada para evitar el '?next=/'
    path('logout/', views.custom_logout_view, name='logout'),
]