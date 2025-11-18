# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout 
from django.urls import reverse 

# ====================================
# 1. VISTAS PÚBLICAS (ACCESO LIBRE)
# Estas vistas renderizan páginas sin requerir autenticación.
# ====================================

def index(request):
    """
    Renderiza la página de inicio principal (index.html).
    Esta es la puerta de entrada pública a la aplicación.
    """
    return render(request, 'core/index.html')

def bienvenido(request):
    """
    Renderiza la página de bienvenida (bienvenidos.html).
    Esta vista puede ser usada después de un login exitoso.
    """
    # Nota: Usamos 'bienvenidos.html' ya que creaste ese archivo.
    return render(request, 'core/bienvenidos.html')


# ====================================
# 2. VISTAS DE AUTENTICACIÓN Y REDIRECCIÓN
# ====================================

# 1. VISTA DE INICIO (Redirige al Dashboard)
@login_required
def home_dashboard(request):
    """
    Si el usuario está logueado, lo redirige al dashboard de inventario.
    """
    # Usamos redirect al nombre de la ruta que definiste en inventario/urls.py
    return redirect('inventario:dashboard')


# 2. VISTA DE LOGOUT PERSONALIZADA (SOLUCIONA EL ?next=/)
def custom_logout_view(request):
    """
    Cierra la sesión y redirige directamente a la página de login.
    Esto asegura que no se use el parámetro 'next'.
    """
    # Llama a la función de logout de Django
    logout(request)
    
    # Redirige a la URL nombrada 'core:login' sin usar el parámetro 'next'.
    return redirect(reverse('core:login'))