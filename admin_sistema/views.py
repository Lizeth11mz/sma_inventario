# C:\Users\ADMIN\Desktop\proyecto\sma_inventario admin_sistema\views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from core.models import PerfilUsuario 
from django.db.models import F 

# 🚨 CORRECCIÓN DEL IMPORTERROR: Importar RelatedObjectDoesNotExist desde el descriptor del campo.
from django.core.exceptions import ObjectDoesNotExist 
RelatedObjectDoesNotExist = ObjectDoesNotExist # Aunque técnicamente es ObjectDoesNotExist, lo redefinimos por consistencia.


# ********************************************************************
# LÓGICA DE PERMISOS (NIVELES DE ACCESO)
# ********************************************************************

# Función de prueba para verificar si el usuario es Administrador (Nivel 1)
def is_admin(user):
    """Retorna True si el usuario está autenticado y tiene Nivel 1 (Administrador)."""
    if not user.is_authenticated:
        return False
    try:
        # Se verifica que el perfil exista y que el nivel sea 1
        return user.perfilusuario.nivel_acceso == 1
    except RelatedObjectDoesNotExist:
        # Si no tiene perfil, se niega el acceso por seguridad
        return False
    except AttributeError:
        # Si el modelo User no tiene el atributo perfilusuario (poco probable si usas select_related)
        return False


# ********************************************************************
# VISTAS DE GESTIÓN DE USUARIOS
# ********************************************************************

# Aplicamos la restricción: solo Administrador (Nivel 1) puede acceder
@login_required
@user_passes_test(is_admin, login_url='/dashboard/') # Redirige al dashboard si el acceso es denegado
def gestion_usuarios(request):
    """Maneja la creación de usuarios (POST) y lista todos (GET)."""
    
    # -----------------------------------------------------
    # Lógica POST: Crear Nuevos Usuarios
    # -----------------------------------------------------
    if request.method == 'POST':
        # 1. Obtener datos del formulario
        username = request.POST.get('usuario')
        first_name = request.POST.get('nombre')
        last_name = request.POST.get('apellidos')
        email = request.POST.get('email') 
        password = request.POST.get('contrasena')
        confirm_password = request.POST.get('confirmar_contrasena')
        
        # Nuevos campos para PerfilUsuario
        nivel = request.POST.get('nivel') # Nivel: 1=Admin, 2=Responsable, 3=Jefe Almacén
        num_empleado = request.POST.get('num_empleado')
        
        # --- VALIDACIONES ---
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden. Por favor, inténtalo de nuevo.')
            return redirect('admin_sistema:usuarios')

        # --- LÓGICA DE CREACIÓN ---
        try:
            # Configuración de permisos de User basada en Nivel
            is_superuser = nivel == '1'
            # Permitimos que Responsable (2) y Admin (1) sean staff, si lo deseas
            is_staff = nivel in ('1', '2') 
            
            # Crear el objeto User 
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_staff=is_staff,
                is_superuser=is_superuser,
            )
            
            # GUARDAR INFORMACIÓN EN EL PERFIL DE USUARIO
            # El perfil debió crearse automáticamente con una señal, pero lo ajustamos
            user.perfilusuario.nivel_acceso = int(nivel) 
            user.perfilusuario.numero_empleado = num_empleado if num_empleado else None 
            user.perfilusuario.save()

            messages.success(request, f'¡Usuario "{username}" creado exitosamente!')
            
        except IntegrityError:
            messages.error(request, f'El nombre de usuario "{username}" ya está registrado o el Email ya existe.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error inesperado al crear el usuario: {e}')
            
        return redirect('admin_sistema:usuarios')

    # -----------------------------------------------------
    # Lógica GET: Mostrar Usuarios
    # -----------------------------------------------------
    # Usamos select_related para obtener el perfil en la misma consulta
    usuarios_listado = User.objects.all().select_related('perfilusuario').order_by('username')
    context = {'usuarios': usuarios_listado}
    
    return render(request, 'admin_sistema/usuarios.html', context)


# Aplicamos la restricción: solo Administrador (Nivel 1) puede acceder
@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def editar_usuario(request, pk):
    """Maneja la edición de un usuario existente (GET y POST)."""
    
    # Intenta obtener el usuario precargando el perfil.
    usuario = get_object_or_404(User.objects.select_related('perfilusuario'), pk=pk)

    if request.method == 'POST':
        # -----------------------------------------------------
        # Lógica POST: Guardar Edición
        # -----------------------------------------------------
        new_first_name = request.POST.get('nombre')
        new_last_name = request.POST.get('apellidos')
        new_email = request.POST.get('email')
        new_password = request.POST.get('contrasena')
        confirm_password = request.POST.get('confirmar_contrasena')
        new_nivel = request.POST.get('nivel')
        new_estado = request.POST.get('estado')
        new_num_empleado = request.POST.get('num_empleado')
        
        # Validar cambio de contraseña
        if new_password and new_password != confirm_password:
            messages.error(request, 'Las contraseñas nuevas no coinciden.')
            return redirect('admin_sistema:editar_usuario', pk=pk)
        
        # 2. Actualizar campos del modelo User
        usuario.first_name = new_first_name
        usuario.last_name = new_last_name
        usuario.email = new_email 
        usuario.is_active = new_estado == 'Activo'
        
        # 3. Actualizar contraseña solo si se proporciona
        if new_password:
            usuario.set_password(new_password)
        
        # 4. Actualizar permisos (is_staff/is_superuser) basados en el Nivel
        usuario.is_superuser = new_nivel == '1'
        usuario.is_staff = new_nivel in ('1', '2') 
        
        # 5. Guardar el objeto User y Perfil
        try:
            usuario.save() # Guarda los campos de User
            
            # Obtener/Crear perfil si no existe antes de actualizarlo
            try:
                perfil = usuario.perfilusuario
            except RelatedObjectDoesNotExist:
                # Si no existe, lo creamos con un nivel base por defecto (ej. Nivel 4)
                perfil = PerfilUsuario.objects.create(user=usuario, nivel_acceso=4)
            
            # Actualizar el PerfilUsuario
            perfil.nivel_acceso = int(new_nivel)
            perfil.numero_empleado = new_num_empleado if new_num_empleado else None 
            perfil.save() # Guarda los campos de PerfilUsuario
            
            messages.success(request, f'Usuario "{usuario.username}" modificado exitosamente.')
        except IntegrityError:
            messages.error(request, f'Error: El nombre de usuario "{usuario.username}" ya existe o el Email ya está registrado.')
            return redirect('admin_sistema:editar_usuario', pk=pk)
        except Exception as e:
            messages.error(request, f'Error al guardar: {e}')
            
        return redirect('admin_sistema:usuarios')

    # -----------------------------------------------------
    # Lógica GET: Mostrar Formulario
    # -----------------------------------------------------
    
    # Manejar el caso donde el perfil no existe
    try:
        num_empleado_actual = usuario.perfilusuario.numero_empleado
    except RelatedObjectDoesNotExist:
        # El perfil no existe. Lo creamos.
        PerfilUsuario.objects.create(user=usuario, nivel_acceso=4)
        messages.warning(request, f'Perfil de usuario para "{usuario.username}" creado automáticamente. Por favor, verifique el Nivel y el # Empleado.')
        
        # Recargamos el objeto para obtener el dato recién creado
        usuario = get_object_or_404(User.objects.select_related('perfilusuario'), pk=pk)
        num_empleado_actual = usuario.perfilusuario.numero_empleado
    
    context = {
        'usuario': usuario,
        'num_empleado_actual': num_empleado_actual, # Se envía al template
    }
    
    return render(request, 'admin_sistema/editar_usuario.html', context)


# Aplicamos la restricción: solo Administrador (Nivel 1) puede acceder
@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def eliminar_usuario(request, pk):
    """Maneja la eliminación de un usuario."""
    usuario = get_object_or_404(User, pk=pk)
    username = usuario.username

    # Restricciones de eliminación (Superusuario y usuario activo)
    if usuario.is_superuser:
        messages.error(request, f'No se puede eliminar a un Superusuario.')
        return redirect('admin_sistema:usuarios')
    
    if request.user.pk == usuario.pk:
        messages.error(request, 'No puedes eliminar tu propia cuenta mientras está activa.')
        return redirect('admin_sistema:usuarios')

    try:
        usuario.delete()
        messages.success(request, f'Usuario "{username}" eliminado correctamente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar el usuario: {e}')

    return redirect('admin_sistema:usuarios')


# ********************************************************************
# VISTAS PLACEHOLDER (CON RESTRICCIÓN DE ACCESO)
# ********************************************************************

# Solo el Administrador (Nivel 1) puede acceder a Proveedores
@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def gestion_proveedores(request):
    """Muestra la interfaz para gestionar proveedores."""
    return render(request, 'admin_sistema/proveedores.html', {})

# Solo el Administrador (Nivel 1) puede acceder a Reportes
@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def generar_reportes(request):
    """Muestra la interfaz para generar reportes."""
    return render(request, 'admin_sistema/reportes.html', {})