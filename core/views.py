# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout # ⬅️ Necesario para cerrar la sesión
from django.urls import reverse         # ⬅️ Necesario para la redirección controlada

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