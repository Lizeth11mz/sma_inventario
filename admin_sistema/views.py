# C:\Users\ADMIN\Desktop\proyecto\sma_inventario\admin_sistema\views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from core.models import PerfilUsuario 
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist

# Corrección para evitar error cuando no existe perfil
RelatedObjectDoesNotExist = ObjectDoesNotExist


# =======================================================
# 🔐  VALIDACIÓN DE PERMISOS
# =======================================================

def is_admin(user):
    """Retorna True si el usuario tiene nivel 1 (Administrador)."""
    if not user.is_authenticated:
        return False
    try:
        return user.perfilusuario.nivel_acceso == 1
    except RelatedObjectDoesNotExist:
        return False
    except AttributeError:
        return False


# =======================================================
# 🔵  VISTAS DE LOGIN SEGÚN TIPO DE USUARIO (PLACEHOLDERS)
# =======================================================

def login_admin(request):
    """Login para administradores."""
    return render(request, 'admin_sistema/login_admin.html', {})

def login_warehouse(request):
    """Login para jefes/encargados de almacén."""
    return render(request, 'admin_sistema/login_warehouse.html', {})

def login_user(request):
    """Login para usuarios generales."""
    return render(request, 'admin_sistema/login_user.html', {})


# =======================================================
# 🟦  CRUD DE USUARIOS (LISTAR, CREAR, EDITAR, ELIMINAR)
# =======================================================

@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def gestion_usuarios(request):
    """Lista usuarios y permite crear nuevos."""
    
    if request.method == 'POST':
        username = request.POST.get('usuario')
        first_name = request.POST.get('nombre')
        last_name = request.POST.get('apellidos')
        email = request.POST.get('email')
        password = request.POST.get('contrasena')
        confirm_password = request.POST.get('confirmar_contrasena')
        nivel = request.POST.get('nivel')
        num_empleado = request.POST.get('num_empleado')
        
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('admin_sistema:usuarios')

        try:
            is_superuser = nivel == '1'
            is_staff = nivel in ('1', '2')
            
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_staff=is_staff,
                is_superuser=is_superuser,
            )

            # Guardar perfil
            user.perfilusuario.nivel_acceso = int(nivel)
            user.perfilusuario.numero_empleado = num_empleado if num_empleado else None
            user.perfilusuario.save()

            messages.success(request, f'Usuario "{username}" creado exitosamente.')

        except IntegrityError:
            messages.error(request, f'El usuario "{username}" o el email ya existen.')
        except Exception as e:
            messages.error(request, f'Error inesperado: {e}')
        
        return redirect('admin_sistema:usuarios')
    
    # Listado GET
    usuarios_listado = User.objects.all().select_related('perfilusuario').order_by('username')
    return render(request, 'admin_sistema/usuarios.html', {"usuarios": usuarios_listado})


@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def editar_usuario(request, pk):
    """Editar usuario existente."""
    
    usuario = get_object_or_404(User.objects.select_related('perfilusuario'), pk=pk)

    if request.method == 'POST':
        new_first_name = request.POST.get('nombre')
        new_last_name = request.POST.get('apellidos')
        new_email = request.POST.get('email')
        new_password = request.POST.get('contrasena')
        confirm_password = request.POST.get('confirmar_contrasena')
        new_nivel = request.POST.get('nivel')
        new_estado = request.POST.get('estado')
        new_num_empleado = request.POST.get('num_empleado')
        
        if new_password and new_password != confirm_password:
            messages.error(request, 'Las contraseñas nuevas no coinciden.')
            return redirect('admin_sistema:editar_usuario', pk=pk)

        usuario.first_name = new_first_name
        usuario.last_name = new_last_name
        usuario.email = new_email
        usuario.is_active = new_estado == 'Activo'

        if new_password:
            usuario.set_password(new_password)

        usuario.is_superuser = new_nivel == '1'
        usuario.is_staff = new_nivel in ('1', '2')

        try:
            usuario.save()

            try:
                perfil = usuario.perfilusuario
            except RelatedObjectDoesNotExist:
                perfil = PerfilUsuario.objects.create(user=usuario, nivel_acceso=4)

            perfil.nivel_acceso = int(new_nivel)
            perfil.numero_empleado = new_num_empleado if new_num_empleado else None
            perfil.save()

            messages.success(request, f'Usuario "{usuario.username}" actualizado.')

        except IntegrityError:
            messages.error(request, 'El usuario o email ya existen.')
        except Exception as e:
            messages.error(request, f'Error al guardar: {e}')

        return redirect('admin_sistema:usuarios')

    try:
        num_empleado_actual = usuario.perfilusuario.numero_empleado
    except RelatedObjectDoesNotExist:
        PerfilUsuario.objects.create(user=usuario, nivel_acceso=4)
        num_empleado_actual = None

    return render(request, 'admin_sistema/editar_usuario.html', {
        'usuario': usuario,
        'num_empleado_actual': num_empleado_actual
    })


@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def eliminar_usuario(request, pk):
    """Eliminar usuario por ID."""

    usuario = get_object_or_404(User, pk=pk)
    
    if usuario.is_superuser:
        messages.error(request, "No se puede eliminar un superusuario.")
        return redirect('admin_sistema:usuarios')

    if request.user.pk == usuario.pk:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
        return redirect('admin_sistema:usuarios')

    try:
        usuario.delete()
        messages.success(request, f'Usuario "{usuario.username}" eliminado.')
    except Exception as e:
        messages.error(request, f'Error al eliminar: {e}')

    return redirect('admin_sistema:usuarios')


# =======================================================
# 🧾  PROVEEDORES Y REPORTES (PLACEHOLDER)
# =======================================================

@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def gestion_proveedores(request):
    return render(request, 'admin_sistema/proveedores.html', {})

@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def generar_reportes(request):
    return render(request, 'admin_sistema/reportes.html', {})
