# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from core.models import PerfilUsuario # Asegúrate de que este modelo exista

# ============================================================
# 1. VISTAS PÚBLICAS
# ============================================================

def index(request):
    """
    Página principal. Si el usuario ya está autenticado, redirige al dashboard.
    Ruta: /
    """
    if request.user.is_authenticated:
        # Redirige a la vista del dashboard después de un login exitoso
        # Usamos home_dashboard ya que esta es la ruta común que maneja la lógica de redirección por nivel.
        return redirect('core:dashboard') 
        
    return render(request, 'core/index.html')


def bienvenido(request):
    """Página donde se elige el rol (Administrador / Responsable / Jefe)."""
    # Nota: El template usado es 'core/bienvenidos.html', asegúrate que exista.
    return render(request, 'core/bienvenidos.html')


# ============================================================
# 2. LOGIN UNIVERSAL PARA LOS 3 ROLES
# ============================================================

def login_view(request):
    # La lógica para usar una vista custom de login con múltiples roles es compleja
    # si se usa junto con django.contrib.auth.views.LoginView en urls.py.
    # Esta función parece replicar o reemplazar la funcionalidad de LoginView.

    rol = request.GET.get("role", None)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Usuario o contraseña incorrectos.")
            # Asegúrate de volver a pasar el parámetro 'role' si es necesario
            return render(request, "core/login.html", {'role': rol})

        # Verificar si tiene perfil
        try:
            nivel = user.perfilusuario.nivel_acceso
        except PerfilUsuario.DoesNotExist:
            messages.error(request, "El usuario no tiene un perfil de acceso.")
            return render(request, "core/login.html", {'role': rol})

        # ============================================================
        # VALIDACIÓN SEGÚN BOTÓN DE ACCESO
        # ============================================================

        if rol == "admin" and nivel != 1:
            messages.error(request, "Este acceso es exclusivo para Administradores.")
            return render(request, "core/login.html", {'role': rol})

        if rol == "responsable" and nivel != 2:
            messages.error(request, "Este acceso es exclusivo para Responsables de Área.")
            return render(request, "core/login.html", {'role': rol})

        if rol == "jefe" and nivel != 3:
            messages.error(request, "Este acceso es exclusivo para Jefes de Almacén.")
            return render(request, "core/login.html", {'role': rol})

        # Login válido
        login(request, user)
        messages.success(request, f"¡Bienvenido, {user.username}!")


        # ============================================================
        # REDIRECCIÓN SEGÚN NIVEL DE ACCESO
        # ============================================================

        # Nota: La redirección en una vista custom de login sobrescribe LOGIN_REDIRECT_URL
        if nivel == 1:
            return redirect("admin_sistema:usuarios")

        elif nivel == 2:
            return redirect("inventario:dashboard_responsable")

        elif nivel == 3:
            return redirect("inventario:dashboard_jefe")
        
        # En caso de que el nivel no esté definido, redirigir al dashboard genérico
        return redirect("core:dashboard")

    return render(request, "core/login.html")


# ============================================================
# 3. DASHBOARD Y LOGOUT
# ============================================================

@login_required
def home_dashboard(request):
    """
    Dashboard genérico. Redirige al dashboard específico según el nivel.
    Ruta: /dashboard/
    """
    try:
        nivel = request.user.perfilusuario.nivel_acceso
        if nivel == 1:
            return redirect("admin_sistema:usuarios")
        elif nivel == 2:
            return redirect("inventario:dashboard_responsable")
        elif nivel == 3:
            return redirect("inventario:dashboard_jefe")
    except (PerfilUsuario.DoesNotExist, AttributeError):
        # Si no hay perfil, lo enviamos al login o a una página de error/aviso
        messages.error(request, "Tu cuenta no tiene un nivel de acceso asignado.")
        return redirect('core:login')

    # Redirección de fallback si algo falla, envía al dashboard principal de inventario
    return redirect("inventario:dashboard")


def custom_logout_view(request):
    """
    Cierra la sesión y redirige a la página principal (core:index).
    Ruta: /logout/
    """
  
    logout(request)
    
    # Redirigimos al nombre de la ruta que apunta a la raíz: core:index
    return redirect(reverse("core:index"))