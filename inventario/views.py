from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.db.models import Q, Sum 
from django.utils import timezone 
import uuid 
from django.views.decorators.http import require_POST 
from decimal import Decimal # Importar Decimal para manejo preciso de cantidades

# Importa SOLO los modelos que existen en models.py.
from .models import ElementoInventario, ClaseInventario, Proveedor, MovimientoInventario 

# -----------------------------------------------------------------------------
# 🚀 VISTA DE DASHBOARD (Optimización Aplicada)
# -----------------------------------------------------------------------------

@login_required
def inventario_dashboard(request):
    """Muestra el inventario general (stock actual) y el registro de movimientos, aplicando filtrado."""
    
    current_search = request.GET.get('busqueda', '').strip()
    current_filter = request.GET.get('filtro_por', 'Descripcion')
    
    # --- 1. Inicializar QuerySets BASE y Optimizar la Carga de Datos ---
    
    # Inventario: Optimizada (clase)
    inventario_base = ElementoInventario.objects.select_related('clase')
    
    # ✅ MOVIMIENTOS: Optimizada para el Elemento (ubicacion) y el Responsable (nombre)
    movimientos_base = MovimientoInventario.objects.select_related(
        'elemento', 
        'responsable'
    ).order_by('-fecha_movimiento')
    
    inventario_list = inventario_base
    movimientos_list = movimientos_base
    
    # --- 2. Aplicar el filtrado SÓLO si hay un término de búsqueda ---
    if current_search:
        
        # A. Filtros para INVENTARIO (ElementoInventario)
        if current_filter == 'Descripcion':
            inventario_list = inventario_list.filter(
                descripcion__icontains=current_search
            ).order_by('descripcion')
            # 💡 Mejora: Si se filtra el inventario, los movimientos se mantienen recientes (últimos 50)
            movimientos_list = movimientos_base[:50] 

        elif current_filter == 'Clase':
            inventario_list = inventario_list.filter(
                clase__nombre__icontains=current_search
            ).order_by('descripcion')
            movimientos_list = movimientos_base[:50] 
        
        # B. Filtros para MOVIMIENTOS (MovimientoInventario)
        elif current_filter == 'Elemento':
            movimientos_list = movimientos_list.filter(
                elemento__descripcion__icontains=current_search
            ).order_by('-fecha_movimiento') 
            # 💡 Mejora: Si se filtra por movimiento, se mantiene el inventario completo.
            inventario_list = inventario_base.order_by('id') 

        elif current_filter == 'Destino':
            movimientos_list = movimientos_list.filter(
                referencia__icontains=current_search
            ).order_by('-fecha_movimiento') 
            inventario_list = inventario_base.order_by('id') 
        
        # ✅ NUEVO FILTRO: Ubicación/Almacén. Agregado para usar el campo nuevo.
        elif current_filter == 'Ubicacion':
            # Se filtra el inventario que coincide con la ubicación
            inventario_list = inventario_list.filter(
                ubicacion__icontains=current_search
            ).order_by('descripcion')
            # Y se muestran los movimientos más recientes
            movimientos_list = movimientos_base[:50] 
            
    # --- 3. Aplicar ordenamiento y limitación si NO hay búsqueda ---
    else:
        inventario_list = inventario_list.order_by('id')
        movimientos_list = movimientos_list[:50] 
        
    context = {
        'inventario_list': inventario_list,
        'movimientos_list': movimientos_list,
        'current_search': current_search,
        'current_filter': current_filter,
    }
    return render(request, 'inventario/dashboard.html', context)

# -----------------------------------------------------------------------------
# 🟢 VISTA DE ENTRADAS (gestion_entradas)
# -----------------------------------------------------------------------------

@login_required
def gestion_entradas(request):
    """Gestiona la adición de múltiples entradas de inventario a través de un carrito temporal."""
    
    SESSION_KEY = 'entradas_temp' 
    entradas_temporales = request.session.get(SESSION_KEY, [])

    if request.method == 'POST':
        if 'confirmar_entradas' in request.POST:
            return _confirmar_entradas(request, SESSION_KEY, entradas_temporales)
        elif 'agregar_item' in request.POST:
            return _agregar_entrada_temporal(request, SESSION_KEY, entradas_temporales)
        elif 'eliminar_item' in request.POST:
            return _eliminar_item_temporal(request, SESSION_KEY, entradas_temporales) 

    # --- LÓGICA DE RENDERIZADO (GET) ---
    elementos = ElementoInventario.objects.select_related('clase').order_by('descripcion')
    proveedores = Proveedor.objects.all().order_by('nombre')
    clases = ClaseInventario.objects.all().order_by('id') 

    context = {
        'elementos': elementos,
        'proveedores': proveedores, 
        'clases': clases,
        'entradas_temporales': entradas_temporales, 
    }
    return render(request, 'inventario/entradas.html', context)


# -----------------------------------------------------------------------------
# 🔴 VISTA DE SALIDAS (gestion_salidas)
# -----------------------------------------------------------------------------

@login_required
def gestion_salidas(request):
    """
    Gestiona la adición de múltiples salidas de inventario a través
    de un carrito temporal en la sesión.
    """
    
    SESSION_KEY = 'salidas_temp' 
    salidas_temporales = request.session.get(SESSION_KEY, [])

    if request.method == 'POST':
        if 'confirmar_salidas' in request.POST:
            return _confirmar_salidas(request, SESSION_KEY, salidas_temporales)
        elif 'agregar_item' in request.POST:
            return _agregar_salida_temporal(request, SESSION_KEY, salidas_temporales)
        elif 'eliminar_item' in request.POST:
            return _eliminar_item_temporal(request, SESSION_KEY, salidas_temporales) 

    # --- LÓGICA DE RENDERIZADO (GET) ---
    elementos = ElementoInventario.objects.select_related('clase').order_by('descripcion')
    clases = ClaseInventario.objects.all().order_by('id') 

    context = {
        'elementos': elementos,
        'clases': clases,
        'salidas_temporales': salidas_temporales, 
    }
    return render(request, 'inventario/salidas.html', context)


# -----------------------------------------------------------------------------
# 📦 OTRAS VISTAS (CRUD Proveedores, etc.)
# -----------------------------------------------------------------------------

@login_required
def gestion_inventario(request):
    messages.info(request, "Vista de Gestión de Inventario (CRUD) en desarrollo.")
    return redirect('inventario:dashboard') 

@login_required
def crear_producto(request):
    """Vista principal para manejar el POST del modal 'Nuevo Producto'."""
    return _crear_nuevo_producto_logica(request) 


@login_required
def gestion_reportes(request):
    messages.info(request, "Vista de Reportes en desarrollo.")
    return render(request, 'inventario/reportes.html', {}) 

# --- GESTIÓN DE PROVEEDORES (CREAR Y LISTAR) ---
@login_required
def gestion_proveedores(request):
    """Maneja la creación de Proveedores y lista todos los proveedores."""
    
    if request.method == 'POST':
        # --- CREAR PROVEEDOR ---
        nombre = request.POST.get('nombre', '').strip()
        rfc = request.POST.get('rfc', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        giro = request.POST.get('giro', '').strip()
        contacto = request.POST.get('contacto', '').strip() 
        activo_str = request.POST.get('activo', 'True') 
        activo = activo_str == 'True'

        if not nombre:
            messages.error(request, "El **Nombre** del proveedor es obligatorio.")
            return redirect('inventario:proveedores')

        try:
            Proveedor.objects.create(
                nombre=nombre,
                rfc=rfc,
                direccion=direccion, 
                giro=giro, 
                contacto=contacto,
                activo=activo
            )
            messages.success(request, f"Proveedor **'{nombre}'** registrado con éxito.")
        except Exception as e:
            messages.error(request, f"Error al registrar el proveedor: {e}")
            
        return redirect('inventario:proveedores')
    
    # --- LÓGICA DE RENDERIZADO (GET) ---
    proveedores = Proveedor.objects.all().order_by('nombre')
    context = {
        'proveedores': proveedores
    }
    return render(request, 'inventario/proveedores.html', context)

# --- VISTA DE EDICIÓN DE PROVEEDOR ---
@login_required
def editar_proveedor(request, proveedor_id): 
    """Permite editar un proveedor existente."""
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        rfc = request.POST.get('rfc', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        giro = request.POST.get('giro', '').strip()
        contacto = request.POST.get('contacto', '').strip()
        activo_str = request.POST.get('activo', 'False') 
        activo = activo_str == 'True'

        if not nombre:
            messages.error(request, "El Nombre del proveedor es obligatorio.")
            return redirect('inventario:proveedor_editar', proveedor_id=proveedor_id)
            
        try:
            # Actualizar el objeto Proveedor
            proveedor.nombre = nombre
            proveedor.rfc = rfc
            proveedor.direccion = direccion
            proveedor.giro = giro
            proveedor.contacto = contacto
            proveedor.activo = activo
            proveedor.save()

            messages.success(request, f"Proveedor **'{nombre}'** actualizado con éxito.")
            return redirect('inventario:proveedores')

        except Exception as e:
            messages.error(request, f"Error al actualizar el proveedor: {e}")
            
    context = {
        'proveedor': proveedor,
    }
    return render(request, 'inventario/proveedor_editar.html', context)

# --- VISTA DE ELIMINACIÓN DE PROVEEDOR ---
@login_required
@require_POST
def eliminar_proveedor(request, proveedor_id): 
    """Elimina un proveedor de la base de datos (POST method requerido)."""
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    nombre = proveedor.nombre
    
    try:
        proveedor.delete()
        messages.success(request, f"Proveedor **'{nombre}'** eliminado con éxito.")
    except Exception as e:
        messages.error(request, f"Error al eliminar el proveedor: {e}")
        
    return redirect('inventario:proveedores')


# -----------------------------------------------------------------------------
# 🛠️ FUNCIONES AUXILIARES GENERALES
# -----------------------------------------------------------------------------

def _crear_nuevo_producto_logica(request):
    """Procesa el formulario del modal 'Nuevo Producto'."""
    if request.method != 'POST':
        messages.error(request, "Método no permitido. Use el formulario de creación de producto.")
        return redirect(request.META.get('HTTP_REFERER', 'inventario:dashboard'))

    descripcion = request.POST.get('descripcion')
    clase_id = request.POST.get('clase_id') 
    unidad = request.POST.get('unidad') 
    ubicacion = request.POST.get('ubicacion', '').strip() # Obtener el nuevo campo
    
    costo_str = request.POST.get('costo_unitario', '0.0').replace(',', '.') # Manejo de decimales

    if not all([descripcion, clase_id, unidad]):
        messages.error(request, "Los campos **Descripción, Unidad y Clase** son obligatorios para crear un nuevo producto.")
        return redirect(request.META.get('HTTP_REFERER', 'inventario:dashboard'))

    try:
        clase = get_object_or_404(ClaseInventario, pk=clase_id)
        costo = Decimal(costo_str) # Usar Decimal para consistencia
        
        if costo < 0:
            messages.error(request, "El costo unitario no puede ser negativo.")
            return redirect(request.META.get('HTTP_REFERER', 'inventario:dashboard'))

        nuevo_elemento = ElementoInventario.objects.create(
            descripcion=descripcion,
            clase=clase,
            unidad=unidad,
            costo_unitario=costo, 
            ubicacion=ubicacion, # ✅ Incluir el campo Ubicación al crear
            stock_actual=Decimal('0.00'), # Inicializa el stock en cero con Decimal
        )
        messages.success(request, f"Producto '{nuevo_elemento.descripcion}' creado con éxito.")
        
    except ValueError:
        messages.error(request, "El costo debe ser un número válido.")
    except IntegrityError:
        messages.error(request, f"Error: Ya existe un producto con la descripción '{descripcion}'.")
    except Exception as e:
        messages.error(request, f"Error al crear el producto: {e}")
        
    return redirect(request.META.get('HTTP_REFERER', 'inventario:dashboard'))


def _eliminar_item_temporal(request, SESSION_KEY, items_temporales):
    """Función unificada para eliminar un ítem de la sesión (carrito)."""
    item_index = request.POST.get('item_index')
    
    # Se añade validación de None por si la clave no existe
    if items_temporales is None: 
        messages.error(request, "No hay elementos temporales para eliminar.")
        return redirect(request.META.get('HTTP_REFERER', 'inventario:dashboard'))

    try:
        index = int(item_index)
        if 0 <= index < len(items_temporales):
            del items_temporales[index]
            request.session[SESSION_KEY] = items_temporales
            request.session.modified = True
            messages.warning(request, "Elemento temporal eliminado.")
        else:
            messages.error(request, "Índice de elemento no válido.")
    except (ValueError, TypeError):
        messages.error(request, "Índice de elemento no válido.")
        
    return redirect(request.META.get('HTTP_REFERER', 'inventario:dashboard'))

# -----------------------------------------------------------------------------
# 🛠️ FUNCIONES AUXILIARES DE ENTRADAS
# -----------------------------------------------------------------------------

def _obtener_folio_y_fecha(request, SESSION_KEY):
    """Genera un folio y fecha únicos para el lote de ENTRADA."""
    LOTE_KEY = f'{SESSION_KEY}_lote'
    lote_info = request.session.get(LOTE_KEY)
    
    if not lote_info:
        # Generar un nuevo folio y fecha
        folio_generado = f"ENT-{uuid.uuid4().hex[:8].upper()}" 
        fecha_actual = timezone.now()
        fecha_formato = fecha_actual.strftime('%d/%m/%Y %H:%M')
        
        lote_info = {
            'folio': folio_generado,
            'fecha': fecha_formato,
        }
        # Nota: Aquí se guardan los STR, no hay problema de serialización.
        request.session[LOTE_KEY] = lote_info
        request.session.modified = True
        
    return lote_info['folio'], lote_info['fecha']


def _agregar_entrada_temporal(request, SESSION_KEY, entradas_temporales):
    """Lógica para agregar un ítem al carrito temporal de Entrada (Sesión)."""
    elemento_id = request.POST.get('descripcion')
    cantidad_str = request.POST.get('cantidad')
    proveedor_id = request.POST.get('proveedor_id')

    if not all([elemento_id, cantidad_str, proveedor_id]):
        messages.error(request, "Faltan datos requeridos (Descripción, Cantidad o Proveedor).")
        return redirect('inventario:entradas')

    try:
        folio_automatico, fecha_automatica = _obtener_folio_y_fecha(request, SESSION_KEY)
        
        elemento = get_object_or_404(ElementoInventario, pk=elemento_id)
        proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
        
        # 1. Usar Decimal para el cálculo y validación
        cantidad_decimal = Decimal(cantidad_str.replace(',', '.')) 
        
        if cantidad_decimal <= 0:
            messages.error(request, "La cantidad de entrada debe ser positiva.")
            return redirect('inventario:entradas')
            
        precio_unitario_decimal = getattr(elemento, 'costo_unitario', Decimal('0.00')) 
        
        item_temporal = {
            'id_elemento': elemento.id,
            'descripcion': elemento.descripcion,
            'rubro': elemento.clase.nombre,
            'unidad': elemento.unidad,
            # ✅ CORRECTO: Convertir Decimal a str para la sesión
            'cantidad': str(cantidad_decimal), 
            'precio_unitario': str(precio_unitario_decimal), 
            'id_proveedor': proveedor.id,
            'nombre_proveedor': proveedor.nombre,
            'rfc': getattr(proveedor, 'rfc', ''),
            'folio': folio_automatico, 
            'fecha': fecha_automatica, 
        }
        
        entradas_temporales.append(item_temporal)
        request.session[SESSION_KEY] = entradas_temporales
        request.session.modified = True
        
        messages.info(request, f"'{elemento.descripcion}' agregado al lote con Folio {folio_automatico}.")
        
    except ValueError:
        messages.error(request, "La cantidad o el costo deben ser números válidos.")
    except Exception as e:
        messages.error(request, f"Error al procesar el ítem: {e}")
        
    return redirect('inventario:entradas')


def _confirmar_entradas(request, SESSION_KEY, entradas_temporales):
    """Lógica para guardar todos los ítems de ENTRADA en la base de datos y sumar stock."""
    LOTE_KEY = f'{SESSION_KEY}_lote'
    
    if not entradas_temporales:
        messages.error(request, "No hay elementos para confirmar la entrada.")
        return redirect('inventario:entradas')

    try:
        with transaction.atomic():
            for item in entradas_temporales:
                # 1. Convertir str de vuelta a Decimal para DB y cálculos
                cantidad_db = Decimal(item['cantidad'])
                precio_unitario_db = Decimal(item.get('precio_unitario', '0.00'))
                
                # Usar select_for_update para prevenir condiciones de carrera al modificar el stock
                elemento = ElementoInventario.objects.select_for_update().get(pk=item['id_elemento'])
                proveedor = get_object_or_404(Proveedor, pk=item['id_proveedor'])
                
                # Crear el Movimiento de Inventario
                MovimientoInventario.objects.create(
                    elemento=elemento,
                    tipo='ENTRADA',
                    cantidad=cantidad_db, # Usamos el Decimal
                    precio_unitario=precio_unitario_db, # Usamos el Decimal
                    fecha_movimiento=timezone.now(),
                    responsable=request.user,
                    proveedor=proveedor,
                    folio_documento=item.get('folio', ''), 
                )

                # ⚠️ CORRECCIÓN CLAVE para evitar el error 'float' and 'decimal.Decimal'
                # 1. Aseguramos que el stock actual es un Decimal, incluso si la DB lo devuelve como float/None.
                stock_actual_decimal = Decimal(elemento.stock_actual) if elemento.stock_actual is not None else Decimal('0.00')

                # 2. Realizamos la suma.
                elemento.stock_actual = stock_actual_decimal + cantidad_db
                # -----------------------------------------------------------
                
                # 💡 Opcional: Actualizar el costo unitario del maestro
                # elemento.costo_unitario = precio_unitario_db
                
                elemento.save()
            
            # Limpiar la sesión después de confirmar
            request.session.pop(SESSION_KEY, None)
            request.session.pop(LOTE_KEY, None)
            request.session.modified = True
            
            messages.success(request, f"Entradas registradas y confirmadas con éxito. {len(entradas_temporales)} ítems procesados.")
        
    except Exception as e:
        messages.error(request, f"Error al confirmar las entradas. Transacción revertida. Detalle: {e}")
        
    return redirect('inventario:entradas')

# -----------------------------------------------------------------------------
# 🛠️ FUNCIONES AUXILIARES DE SALIDAS
# -----------------------------------------------------------------------------

def _agregar_salida_temporal(request, SESSION_KEY, salidas_temporales):
    """
    Lógica para agregar un ítem al carrito temporal de Salida (Sesión)
    VALIDANDO el stock actual.
    """
    elemento_id = request.POST.get('descripcion')
    cantidad_str = request.POST.get('cantidad')
    destino_referencia = request.POST.get('destino_referencia')

    if not all([elemento_id, cantidad_str, destino_referencia]):
        messages.error(request, "Faltan datos requeridos (Descripción, Cantidad o Destino).")
        return redirect('inventario:salidas')

    try:
        elemento = get_object_or_404(ElementoInventario, pk=elemento_id)
        
        # 1. Usar Decimal para el cálculo y validación
        cantidad_decimal = Decimal(cantidad_str.replace(',', '.')) 
        
        # ⚠️ CORRECCIÓN: Aseguramos que stock_actual es Decimal para la validación
        stock_actual = Decimal(elemento.stock_actual) if elemento.stock_actual is not None else Decimal('0.00')

        if cantidad_decimal <= 0:
            messages.error(request, "La cantidad a retirar debe ser positiva.")
            return redirect('inventario:salidas')
            
        # 🚨 Validación de Stock
        if cantidad_decimal > stock_actual:
            messages.error(request, f"Stock insuficiente para '{elemento.descripcion}'. Stock actual: {stock_actual:.2f}")
            return redirect('inventario:salidas')
        
        # Usamos Decimal para consistencia
        costo_unitario_decimal = elemento.costo_unitario if elemento.costo_unitario is not None else Decimal('0.00')
        
        item_temporal = {
            'id_elemento': elemento.id,
            'descripcion': elemento.descripcion,
            'rubro': elemento.clase.nombre,
            'unidad': elemento.unidad,
            # ✅ CORRECTO: Convertir Decimal a str para la sesión
            'cantidad': str(cantidad_decimal),
            'costo_unitario': str(costo_unitario_decimal), # Añadido para posible uso futuro
            'destino_referencia': destino_referencia,
        }
        
        salidas_temporales.append(item_temporal)
        request.session[SESSION_KEY] = salidas_temporales
        request.session.modified = True
        
        messages.info(request, f"'{elemento.descripcion}' agregado temporalmente para salida. Stock a retirar: {cantidad_decimal:.2f}")
        
    except ElementoInventario.DoesNotExist:
        messages.error(request, "El elemento seleccionado no es válido.")
    except ValueError:
        messages.error(request, "La cantidad debe ser un número válido.")
    except Exception as e:
        messages.error(request, f"Error al procesar el ítem: {e}")
        
    return redirect('inventario:salidas')


def _confirmar_salidas(request, SESSION_KEY, salidas_temporales):
    """Lógica para guardar todos los ítems de SALIDA en la base de datos y restar stock."""
    
    if not salidas_temporales:
        messages.error(request, "No hay elementos para confirmar la salida.")
        return redirect('inventario:salidas')

    try:
        with transaction.atomic():
            # Generamos un folio único para todo el lote de movimientos permanentes
            folio_lote_db = f"SAL-{uuid.uuid4().hex[:8].upper()}" 
            
            for item in salidas_temporales:
                # 1. Convertir str de vuelta a Decimal para DB y cálculos
                cantidad_db = Decimal(item['cantidad'])
                costo_unitario_db = Decimal(item.get('costo_unitario', '0.00'))

                # Usar select_for_update para prevenir condiciones de carrera al modificar el stock
                elemento = ElementoInventario.objects.select_for_update().get(pk=item['id_elemento'])
                
                # Crear el Movimiento de Inventario
                MovimientoInventario.objects.create(
                    elemento=elemento,
                    tipo='SALIDA', 
                    cantidad=cantidad_db, # Usamos el Decimal
                    # Se usa el costo unitario actual del elemento, que debería ser el que viene de la sesión
                    precio_unitario=costo_unitario_db, 
                    fecha_movimiento=timezone.now(),
                    responsable=request.user,
                    referencia=item['destino_referencia'], # <-- Aquí SÍ se usa para el Destino
                    folio_documento=folio_lote_db, 
                )

                # ⚠️ CORRECCIÓN CLAVE para evitar el error 'float' and 'decimal.Decimal'
                # 1. Aseguramos que el stock actual es un Decimal.
                stock_actual_decimal = Decimal(elemento.stock_actual) if elemento.stock_actual is not None else Decimal('0.00')
                
                # 2. Restar la cantidad del stock_actual
                elemento.stock_actual = stock_actual_decimal - cantidad_db # <--- Resta corregida
                # -----------------------------------------------------------
                
                # Opcional: Re-validar el stock para evitar inconsistencias (doble chequeo)
                if elemento.stock_actual < 0:
                    # Si esto sucede, se revierte toda la transacción gracias a transaction.atomic()
                    raise IntegrityError(f"Error de Stock: La salida de {item['descripcion']} dejaría el stock en negativo. Por favor, revise el inventario.")

                elemento.save()
            
            # Limpiar la sesión después de confirmar
            request.session.pop(SESSION_KEY, None)
            request.session.modified = True
            
            messages.success(request, f"Salidas registradas y confirmadas con éxito. {len(salidas_temporales)} ítems procesados. Folio de Lote: {folio_lote_db}")
        
    except IntegrityError as e:
        messages.error(request, f"Error crítico de inventario: {e}")
    except Exception as e:
        messages.error(request, f"Error al confirmar las salidas. Transacción revertida. Detalle: {e}")
        
    return redirect('inventario:salidas')