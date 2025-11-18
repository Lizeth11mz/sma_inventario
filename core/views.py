# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from core.models import PerfilUsuario


# ============================================================
# 1. VISTAS PÚBLICAS
# ============================================================

def index(request):
    """Página principal."""
    return render(request, 'core/index.html')


def bienvenido(request):
    """Página donde se elige el rol (Administrador / Responsable / Jefe)."""
    return render(request, 'core/bienvenidos.html')


# ============================================================
# 2. LOGIN UNIVERSAL PARA LOS 3 ROLES
# ============================================================

def login_view(request):

    # Saber cuál botón se presionó:
    # admin / responsable / jefe
    rol = request.GET.get("role", None)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, "core/login.html")

        # Verificar si tiene perfil
        try:
            nivel = user.perfilusuario.nivel_acceso
        except PerfilUsuario.DoesNotExist:
            messages.error(request, "El usuario no tiene un perfil de acceso.")
            return render(request, "core/login.html")

        # ============================================================
        # VALIDACIÓN SEGÚN BOTÓN DE ACCESO
        # ============================================================

        if rol == "admin" and nivel != 1:
            messages.error(request, "Este acceso es exclusivo para Administradores.")
            return render(request, "core/login.html")

        if rol == "responsable" and nivel != 2:
            messages.error(request, "Este acceso es exclusivo para Responsables de Área.")
            return render(request, "core/login.html")

        if rol == "jefe" and nivel != 3:
            messages.error(request, "Este acceso es exclusivo para Jefes de Almacén.")
            return render(request, "core/login.html")

        # Login válido
        login(request, user)

        # ============================================================
        # REDIRECCIÓN SEGÚN NIVEL DE ACCESO
        # ============================================================

        if nivel == 1:
            return redirect("admin_sistema:usuarios")

        elif nivel == 2:
            return redirect("inventario:dashboard_responsable")

        elif nivel == 3:
            return redirect("inventario:dashboard_jefe")

    return render(request, "core/login.html")


# ============================================================
# 3. DASHBOARD Y LOGOUT
# ============================================================

@login_required
def home_dashboard(request):
    """Dashboard genérico."""
    return redirect("inventario:dashboard")


def custom_logout_view(request):
    logout(request)
    return redirect(reverse("core:login"))
