# inventario/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.utils import timezone
from django.http import HttpResponse, FileResponse 
from django.http import HttpResponse, FileResponse, Http404 
from pathlib import Path 
import json
import uuid
from django.views.decorators.http import require_POST
from decimal import Decimal
from datetime import timedelta
import os 
import csv
from django.conf import settings 

# NUEVAS IMPORTACIONES PARA GENERACIÓN DE REPORTES
import io 
from openpyxl import Workbook 

# Importa SOLO los modelos que existen en models.py.
from .models import ElementoInventario, ClaseInventario, Proveedor, MovimientoInventario

# -----------------------------------------------------------------------------
# 🚀 VISTA DE DASHBOARD (Optimización Aplicada)
# (Contenido omitido por ser muy largo y no tener errores en la lógica de reportes)
# -----------------------------------------------------------------------------

@login_required
def inventario_dashboard(request):
    """Muestra el inventario general (stock actual) y el registro de movimientos, aplicando filtrado."""
    
    current_search = request.GET.get('busqueda', '').strip()
    current_filter = request.GET.get('filtro_por', 'Descripcion')
    
    # --- 1. Inicializar QuerySets BASE y Optimizar la Carga de Datos ---
    
    # Inventario: Optimizada (clase)
    inventario_base = ElementoInventario.objects.select_related('clase')
    
    # MOVIMIENTOS: Optimizada para el Elemento (ubicacion) y el Responsable (nombre)
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
            inventario_list = inventario_base.order_by('id') 

        elif current_filter == 'Destino':
            movimientos_list = movimientos_list.filter(
                referencia__icontains=current_search
            ).order_by('-fecha_movimiento') 
            inventario_list = inventario_base.order_by('id') 

        elif current_filter == 'Ubicacion':
            inventario_list = inventario_list.filter(
                ubicacion__icontains=current_search
            ).order_by('descripcion')
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
# ✅ VISTA CORREGIDA 1: DASHBOARD DE REPORTES (KPIs y Gráfico)
# -----------------------------------------------------------------------------

@login_required
def reportes_dashboard(request):
    """
    Calcula KPIs, datos para el gráfico y lista los reportes generados 
    (XLSX, CSV, PDF) para descarga.
    """
    
    # 1. --- Lógica de KPIs ---
    
    # a. Valor Total del Inventario
    valor_inventario_total = ElementoInventario.objects.aggregate(
        total=Sum(F('stock_actual') * F('costo_unitario'))
    )['total'] or Decimal('0.00')
    
    # Rango de tiempo: Últimos 30 días
    hace_30_dias = timezone.now() - timedelta(days=30)
    movimientos_recientes = MovimientoInventario.objects.filter(
        fecha_movimiento__gte=hace_30_dias
    )
    
    # b. Valor de Entradas (Últimos 30 días)
    valor_entradas_recientes = movimientos_recientes.filter(
        tipo='ENTRADA'
    ).aggregate(
        total=Sum(F('cantidad') * F('precio_unitario'))
    )['total'] or Decimal('0.00')
    
    # c. Valor de Salidas (Últimos 30 días)
    valor_salidas_recientes = movimientos_recientes.filter(
        tipo='SALIDA'
    ).aggregate(
        total=Sum(F('cantidad') * F('precio_unitario'))
    )['total'] or Decimal('0.00')
    
    # --- 2. Lógica de Datos para Gráfico (Inventario por Clase) ---
    datos_grafico_qs = ElementoInventario.objects.values(
        nombre_clase=F('clase__nombre')
    ).annotate(
        valor_total_clase=Sum(F('stock_actual') * F('costo_unitario'))
    ).order_by('-valor_total_clase')
    
    datos_grafico = {
        'labels': [item['nombre_clase'] for item in datos_grafico_qs],
        'data': [float(item['valor_total_clase']) for item in datos_grafico_qs],
    }
    
    # -------------------------------------------------------------------------
    # 🎯 CORRECCIÓN: Obtener listado de reportes generados para la tabla 
    # Usando settings.REPORTS_DIR y Pathlib para robustez.
    # -------------------------------------------------------------------------
    REPORTS_DIR = settings.REPORTS_DIR
    archivos_generados = []
    
    # Convertimos la cadena de la ruta en settings a un objeto Path para usar Pathlib.
    reports_path = Path(REPORTS_DIR)
    
    # Verificamos que la carpeta exista antes de intentar leerla
    if reports_path.exists() and reports_path.is_dir():
        # Iteramos sobre los archivos en el directorio
        for file_path in reports_path.iterdir():
            filename = file_path.name
            
            # ✅ CORRECCIÓN CLAVE: Añadir '.csv' al filtro de extensiones
            if filename.lower().endswith(('.xlsx', '.pdf', '.csv')):
                # Intenta obtener la fecha de modificación (fecha de generación)
                try:
                    fecha_mod = timezone.datetime.fromtimestamp(file_path.stat().st_mtime)
                    # Ajustar la fecha a la zona horaria de Django
                    fecha_generacion = timezone.make_aware(fecha_mod, timezone.get_current_timezone())
                except Exception:
                    fecha_generacion = None
                    
                archivos_generados.append({
                    'filename': filename,
                    # El tipo se extrae de la extensión (PDF, XLSX, CSV)
                    'tipo': filename.split('.')[-1].upper(), 
                    'fecha_generacion': fecha_generacion,
                })
    
    # Ordenar por fecha de generación más reciente
    archivos_generados.sort(key=lambda x: x['fecha_generacion'] or timezone.now(), reverse=True) 
    
    # --- 4. Preparar Contexto y Renderizar ---
    
    context = {
        'valor_inventario': valor_inventario_total.quantize(Decimal('0.01')),
        'valor_entradas': valor_entradas_recientes.quantize(Decimal('0.01')),
        'valor_salidas': valor_salidas_recientes.quantize(Decimal('0.01')),
        'datos_grafico_json': json.dumps(datos_grafico),
        'categorias': ClaseInventario.objects.all().order_by('nombre'),
        'archivos_generados': archivos_generados, # Enviamos el listado a la plantilla
    }
    
    return render(request, 'inventario/reportes.html', context)


# -----------------------------------------------------------------------------
# ✅ VISTA DE GENERACIÓN DE ARCHIVO DE REPORTE (INVENTARIO) - Sin cambios funcionales
# -----------------------------------------------------------------------------

@login_required
def generar_reporte(request):
    """
    Genera el reporte de INVENTARIO.
    """
    if request.method == 'GET':
        tipo_reporte = request.GET.get('tipo_reporte', 'Inventario Total')
        # Se agrega 'CSV' como opción por defecto si no se especifica.
        formato = request.GET.get('formato', 'XLSX') 
        
        # --- Lógica de Filtrado de Datos (QuerySet) ---
        reporte_data = ElementoInventario.objects.select_related('clase').all()
        
        # --- Lógica de Generación de Reporte (XLSX/CSV/PDF) ---
        filename = None
        
        if formato == 'XLSX':
            filename = _generar_excel_y_guardar(reporte_data, tipo_reporte) 
            
        elif formato == 'CSV':
            filename = _generar_csv_y_guardar(reporte_data, tipo_reporte) 

        elif formato == 'PDF':
            messages.warning(request, "La generación de PDF requiere implementación.")
            return redirect('inventario:reportes')
        
        # Manejo de redirección
        if filename:
            return redirect('inventario:descargar_reporte', filename=filename) 
        else:
            return redirect('inventario:reportes')
    
    return redirect('inventario:reportes')


# -----------------------------------------------------------------------------
# 🆕 VISTA PARA GENERACIÓN DE REPORTE DE MOVIMIENTOS - Sin cambios funcionales
# -----------------------------------------------------------------------------

@login_required
def generar_reporte_movimientos(request):
    """
    Genera el reporte de MOVIMIENTOS con formato simplificado.
    """
    if request.method == 'GET':
        formato = request.GET.get('formato', 'XLSX')
        
        # --- Lógica de Filtrado de Datos (QuerySet de Movimientos) ---
        try:
            movimientos_data = MovimientoInventario.objects.select_related(
                'elemento' 
            ).order_by('-fecha_movimiento') 
            
            if not movimientos_data.exists():
                return redirect('inventario:reportes')

        except Exception as e:
            print(f"Error en queryset de movimientos: {e}")
            return redirect('inventario:reportes')

        # --- Lógica de Generación de Reporte (XLSX/CSV) ---
        filename = None
        
        if formato == 'XLSX':
            filename = _generar_excel_movimientos_y_guardar(movimientos_data) 
            
        elif formato == 'CSV':
            filename = _generar_csv_movimientos_y_guardar(movimientos_data)
        
        
        # Manejo de redirección para formatos XLSX y CSV
        if filename:
            return redirect('inventario:descargar_reporte', filename=filename) 
        else:
            return redirect('inventario:reportes')

    # Si la solicitud no es GET o si cae por defecto
    return redirect('inventario:reportes')
        
# -----------------------------------------------------------------------------
# 📥 VISTA CORREGIDA 3: DESCARGAR ARCHIVO ESTATICO
# -----------------------------------------------------------------------------

@login_required
def descargar_reporte(request, filename):
    """
    Descarga el archivo generado.
    """
    # 🎯 CORRECCIÓN: Usar settings.REPORTS_DIR y Pathlib
    REPORTS_DIR = Path(settings.REPORTS_DIR)
    file_path = REPORTS_DIR / filename
    
    # ⚠️ Validar que el archivo NO esté fuera del directorio de reportes (Seguridad)
    if not REPORTS_DIR in file_path.resolve().parents:
        raise Http404("El archivo solicitado no está en el directorio de reportes.")

    # Validar que el archivo exista en la ruta esperada
    if not file_path.exists():
        raise Http404("El archivo no existe.")

    # Determinar el content_type
    if filename.lower().endswith('.xlsx'):
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif filename.lower().endswith('.csv'):
        content_type = 'text/csv'
    elif filename.lower().endswith('.pdf'):
        content_type = 'application/pdf'
    else:
        content_type = 'application/octet-stream' 

    try:
        # Abrimos el archivo en modo binario ('rb')
        response = FileResponse(file_path.open('rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    except Exception as e:
        # En caso de error de lectura o permiso, devolvemos a la dashboard
        print(f"Error al descargar: {e}")
        return redirect('inventario:reportes')

# -----------------------------------------------------------------------------

# --- FUNCIÓN AUXILIAR PARA GENERAR EXCEL Y GUARDAR (¡CORREGIDA!) ---

def _generar_excel_y_guardar(reporte_data, tipo_reporte):

    """Genera un archivo XLSX, lo GUARDA en el disco (MEDIA_ROOT/reports)

    y retorna el nombre del archivo generado. """

    try:

        REPORTS_DIR = os.path.join(settings.MEDIA_ROOT, 'reports')

        # Asegurarse de que el directorio de reportes exista

        os.makedirs(REPORTS_DIR, exist_ok=True)

        workbook = Workbook()

        sheet = workbook.active

        sheet.title = "Inventario General"

        # Encabezados SOLICITADOS: ID, Clase, Descripción, Unidad, Existencia, Costo

        headers = [

            "ID", "Clase", "Descripción", "Unidad", "Existencia", "Costo"

        ]

        sheet.append(headers)


        # Llenar datos

        for item in reporte_data:

            # Uso de Decimal para manejar stock y costo, evitando None

            stock = item.stock_actual if item.stock_actual is not None else Decimal('0.00')

            costo = item.costo_unitario if item.costo_unitario is not None else Decimal('0.00')

           

            # Fila de datos con el orden y campos deseados (6 columnas)

            row = [

                item.id,

                item.clase.nombre, # Clase

                item.descripcion, # Descripción

                item.unidad, # Unidad

                float(stock), # Existencia (Stock Actual)

                float(costo), # Costo (Costo Unitario)

            ]

            sheet.append(row)



        # 1. Generar nombre de archivo

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

        filename = f"{tipo_reporte.replace(' ', '_')}_{timestamp}.xlsx"

        file_path = os.path.join(REPORTS_DIR, filename)


        # 2. Guardar el libro directamente en la ruta del disco

        workbook.save(file_path)

        return filename

    except Exception as e:

        # Esto imprimirá el error exacto si ocurre uno, ayudando a la depuración.

        print(f"Error al guardar el archivo de Excel: {e}")

        return None 

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

# --- FUNCIÓN AUXILIAR PARA GENERAR CSV DE INVENTARIO Y GUARDAR ---
def _generar_csv_y_guardar(reporte_data, tipo_reporte):
    """Genera un archivo CSV, lo GUARDA en el disco (MEDIA_ROOT/reports)
    y retorna el nombre del archivo generado.
    """
    try:
        REPORTS_DIR = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(REPORTS_DIR, exist_ok=True)
        
        # 1. Generar nombre de archivo
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        # Cambiamos la extensión a .csv
        filename = f"{tipo_reporte.replace(' ', '_')}_{timestamp}.csv"
        file_path = os.path.join(REPORTS_DIR, filename)

        # 2. Definir encabezados (igual que el XLSX)
        headers = [
            "ID", "Clase", "Descripcion", "Unidad", "Existencia", "Costo"
        ]
        
        # 3. Escribir el archivo CSV
        # Usamos 'w' y 'newline=""' y 'encoding="utf-8"' para compatibilidad
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            # Usamos el delimitador de coma estándar
            writer = csv.writer(csvfile)
            
            # Escribir encabezados
            writer.writerow(headers)
            
            # Escribir datos
            for item in reporte_data:
                stock = item.stock_actual if item.stock_actual is not None else Decimal('0.00')
                costo = item.costo_unitario if item.costo_unitario is not None else Decimal('0.00')
                
                # Fila de datos (similar a XLSX)
                row = [
                    item.id,
                    item.clase.nombre,
                    item.descripcion,
                    item.unidad,
                    float(stock),
                    float(costo),
                ]
                writer.writerow(row)
                
        return filename

    except Exception as e:
        # Aquí también es vital imprimir el error si ocurre
        print(f"Error al guardar el archivo CSV de Inventario: {e}")
        return None
        
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


# --- FUNCIÓN AUXILIAR PARA GENERAR EXCEL DE MOVIMIENTOS Y GUARDAR (FORMATO SIMPLIFICADO) ---


def _generar_excel_movimientos_y_guardar(movimientos_data):
    """Genera un archivo XLSX para movimientos con formato simplificado: 
    Fecha, Ubicación, Destino/Referencia, Cantidad.
    """
    
    tipo_reporte = "Reporte_de_Movimientos_Simplificado" # Usamos underscores directamente

    try:
        REPORTS_DIR = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(REPORTS_DIR, exist_ok=True)
        
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Movimientos Simples"
        
        # 1. ENCABEZADOS DESEADOS
        headers = [
            "Fecha", 
            "Ubicación (Almacén)", 
            "Destino/Referencia", 
            "Elemento", 
            "Cantidad"
        ]
        sheet.append(headers)

        # Llenar datos
        for item in movimientos_data:
            
            # Verificación de la relación crítica
            elemento_descripcion = item.elemento.descripcion if item.elemento else "Elemento Desconocido"
            elemento_ubicacion = item.elemento.ubicacion if item.elemento and item.elemento.ubicacion else "N/A"

            # Conversión y manejo de Nulos
            cantidad = item.cantidad if item.cantidad is not None else Decimal('0.00')
            fecha_str = item.fecha_movimiento.strftime('%Y-%m-%d %H:%M:%S') if item.fecha_movimiento else ""
            
            # Formatear la cantidad para indicar ENTRADA o SALIDA
            if item.tipo == 'SALIDA':
                # Si es salida, la cantidad es negativa
                cantidad_formateada = float(cantidad) * -1
            else:
                # Si es entrada, la cantidad es positiva
                cantidad_formateada = float(cantidad)
            
            # 2. FILA DE DATOS
            row = [
                fecha_str,                             
                elemento_ubicacion,                    # Ubicación (Manejada para evitar None)
                item.referencia or "",                 # Destino/Referencia
                elemento_descripcion,                  # Elemento (Manejada para evitar None)
                cantidad_formateada                    
            ]
            sheet.append(row)

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{tipo_reporte}_{timestamp}.xlsx"
        file_path = os.path.join(REPORTS_DIR, filename)

        workbook.save(file_path)
        return filename

    except Exception as e:
        # Esto imprimirá el error exacto en tu consola de Django
        print(f"Error fatal al generar el Excel de Movimientos: {e}") 
        return None
    

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

# --- FUNCIÓN AUXILIAR PARA GENERAR CSV DE MOVIMIENTOS Y GUARDAR ---
def _generar_csv_movimientos_y_guardar(movimientos_data):
    """Genera un archivo CSV para movimientos con formato simplificado:
    Fecha, Ubicación, Destino/Referencia, Cantidad.
    """
    tipo_reporte = "Reporte_de_Movimientos_Simplificado"

    try:
        REPORTS_DIR = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(REPORTS_DIR, exist_ok=True)
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        # Cambiamos la extensión a .csv
        filename = f"{tipo_reporte}_{timestamp}.csv"
        file_path = os.path.join(REPORTS_DIR, filename)

        # 1. ENCABEZADOS DESEADOS
        headers = [
            "Fecha",
            "Ubicacion (Almacen)",
            "Destino/Referencia",
            "Elemento",
            "Cantidad"
        ]
        
        # 2. Escribir el archivo CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

            # Llenar datos
            for item in movimientos_data:
                elemento_descripcion = item.elemento.descripcion if item.elemento else "Elemento Desconocido"
                # 🚨 CORRECCIÓN APLICADA: Forzar a cadena la relación 'ubicacion' para el CSV writer
                elemento_ubicacion = str(item.elemento.ubicacion) if item.elemento and item.elemento.ubicacion else "N/A"
                
                cantidad = item.cantidad if item.cantidad is not None else Decimal('0.00')
                fecha_str = item.fecha_movimiento.strftime('%Y-%m-%d %H:%M:%S') if item.fecha_movimiento else ""
                
                if item.tipo == 'SALIDA':
                    cantidad_formateada = float(cantidad) * -1
                else:
                    cantidad_formateada = float(cantidad)
                
                # 3. FILA DE DATOS
                row = [
                    fecha_str,
                    elemento_ubicacion,
                    item.referencia or "",
                    elemento_descripcion,
                    cantidad_formateada
                ]
                writer.writerow(row)

        return filename

    except Exception as e:
        # 🚨 DEBUG CRÍTICO: Imprimir el error
        print(f"Error fatal al generar el CSV de Movimientos: {e}")
        return None


# -----------------------------------------------------------------------------
# 🟢 VISTA DE ENTRADAS (gestion_entradas)
# (Contenido omitido por ser muy largo)
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
            return _eliminar_item_temporal(request, SESSION_KEY, entradas_temporales, 'inventario:entradas') 

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
# (Contenido omitido por ser muy largo)
# -----------------------------------------------------------------------------
@login_required
def gestion_salidas(request):
    """Gestiona la adición de múltiples salidas de inventario a través de un carrito temporal en la sesión."""
    
    SESSION_KEY = 'salidas_temp' 
    salidas_temporales = request.session.get(SESSION_KEY, [])

    if request.method == 'POST':
        if 'confirmar_salidas' in request.POST:
            # Llama a la función auxiliar para confirmar salidas
            return _confirmar_salidas(request, SESSION_KEY, salidas_temporales) 
        elif 'agregar_item' in request.POST:
            return _agregar_salida_temporal(request, SESSION_KEY, salidas_temporales)
        elif 'eliminar_item' in request.POST:
            return _eliminar_item_temporal(request, SESSION_KEY, salidas_temporales, 'inventario:salidas') 

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
# (Contenido omitido por ser muy largo)
# -----------------------------------------------------------------------------

@login_required
def gestion_inventario(request):
    messages.info(request, "Vista de Gestión de Inventario (CRUD) en desarrollo.")
    return redirect('inventario:dashboard') 

@login_required
def crear_producto(request):
    """Vista principal para manejar el POST del modal 'Nuevo Producto'."""
    return _crear_nuevo_producto_logica(request) 


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
        activo_str = request.POST.get('activo', 'False') 
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
        activo = activo_str == 'on' # Ajuste común para checkboxes

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
# (Contenido omitido por ser muy largo)
# -----------------------------------------------------------------------------

def _crear_nuevo_producto_logica(request):
    """Procesa el formulario del modal 'Nuevo Producto'."""
    # Uso 'inventario:dashboard' como fallback predeterminado y más seguro.
    fallback_url = 'inventario:dashboard' 
    referer = request.META.get('HTTP_REFERER', fallback_url)

    if request.method != 'POST':
        messages.error(request, "Método no permitido. Use el formulario de creación de producto.")
        return redirect(referer) 

    descripcion = request.POST.get('descripcion')
    clase_id = request.POST.get('clase_id') 
    unidad = request.POST.get('unidad') 
    ubicacion = request.POST.get('ubicacion', '').strip() 
    
    costo_str = request.POST.get('costo_unitario', '0.0').replace(',', '.') 

    if not all([descripcion, clase_id, unidad]):
        messages.error(request, "Los campos **Descripción, Unidad y Clase** son obligatorios para crear un nuevo producto.")
        return redirect(referer)

    try:
        clase = get_object_or_404(ClaseInventario, pk=clase_id)
        costo = Decimal(costo_str) 
        
        if costo < 0:
            messages.error(request, "El costo unitario no puede ser negativo.")
            return redirect(referer)

        nuevo_elemento = ElementoInventario.objects.create(
            descripcion=descripcion,
            clase=clase,
            unidad=unidad,
            costo_unitario=costo, 
            ubicacion=ubicacion, 
            stock_actual=Decimal('0.00'), 
        )
        messages.success(request, f"Producto '{nuevo_elemento.descripcion}' creado con éxito.")
        
    except ValueError:
        messages.error(request, "El costo debe ser un número válido.")
    except IntegrityError:
        messages.error(request, f"Error: Ya existe un producto con la descripción '{descripcion}'.")
    except Exception as e:
        messages.error(request, f"Error al crear el producto: {e}")
        
    return redirect(referer)


def _eliminar_item_temporal(request, SESSION_KEY, items_temporales, redirect_to_url_name):
    """
    Función unificada y CORREGIDA para eliminar un ítem de la sesión (carrito).
    Limpia la clave de lote (para entradas) si el carrito queda vacío.
    """
    item_index = request.POST.get('item_index')
    # Definimos la clave de lote para entradas
    LOTE_KEY = f'{SESSION_KEY}_lote' 
    
    if items_temporales is None or not items_temporales: 
        messages.error(request, "No hay elementos temporales para eliminar.")
        return redirect(redirect_to_url_name)

    try:
        index = int(item_index)
        
        if 0 <= index < len(items_temporales):
            del items_temporales[index]
            request.session[SESSION_KEY] = items_temporales
            request.session.modified = True
            
            messages.warning(request, "Elemento temporal eliminado.")
            
            # Limpiar el folio/lote SOLO si es el carrito de ENTRADAS y queda vacío
            if not items_temporales and SESSION_KEY == 'entradas_temp' and LOTE_KEY in request.session:
                request.session.pop(LOTE_KEY, None)
                messages.info(request, "Folio de lote cancelado (carrito vacío).")
                
        else:
            messages.error(request, "Índice de elemento no válido.")
    except (ValueError, TypeError):
        messages.error(request, "Índice de elemento no válido.")
        
    return redirect(redirect_to_url_name)


# -----------------------------------------------------------------------------
# 🛠️ FUNCIONES AUXILIARES DE ENTRADAS
# (Contenido omitido por ser muy largo)
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
        # Obtener el folio, creándolo si no existe en la sesión
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
            # CORRECTO: Convertir Decimal a str para la sesión
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
        
        messages.info(request, f"'{elemento.descripcion}' agregado al lote con Folio **{folio_automatico}**.")
        
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
                    cantidad=cantidad_db, 
                    precio_unitario=precio_unitario_db, 
                    fecha_movimiento=timezone.now(),
                    responsable=request.user,
                    proveedor=proveedor,
                    folio_documento=item.get('folio', ''), 
                )

                # CORRECCIÓN CLAVE: Aseguramos Decimal y realizamos la suma
                stock_actual_decimal = Decimal(elemento.stock_actual) if elemento.stock_actual is not None else Decimal('0.00')
                elemento.stock_actual = stock_actual_decimal + cantidad_db
                # -----------------------------------------------------------
                
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
# (Contenido omitido por ser muy largo)
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
        
        # CORRECCIÓN: Aseguramos que stock_actual es Decimal para la validación
        stock_actual = Decimal(elemento.stock_actual) if elemento.stock_actual is not None else Decimal('0.00')

        if cantidad_decimal <= 0:
            messages.error(request, "La cantidad a retirar debe ser positiva.")
            return redirect('inventario:salidas')
            
        # Validación de Stock
        if cantidad_decimal > stock_actual:
            messages.error(request, f"Stock insuficiente para '{elemento.descripcion}'. Disponible: {stock_actual}, Solicitado: {cantidad_decimal}.")
            return redirect('inventario:salidas')
            
        precio_unitario_salida = getattr(elemento, 'costo_unitario', Decimal('0.00')) 
        
        item_temporal = {
            'id_elemento': elemento.id,
            'descripcion': elemento.descripcion,
            'rubro': elemento.clase.nombre,
            'unidad': elemento.unidad,
            'cantidad': str(cantidad_decimal), 
            'precio_unitario': str(precio_unitario_salida), 
            'destino_referencia': destino_referencia,
        }
        
        salidas_temporales.append(item_temporal)
        request.session[SESSION_KEY] = salidas_temporales
        request.session.modified = True
        
        messages.info(request, f"'{elemento.descripcion}' agregado al carrito de salidas.")
        
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
            for item in salidas_temporales:
                # 1. Convertir str de vuelta a Decimal para DB y cálculos
                cantidad_db = Decimal(item['cantidad'])
                precio_unitario_db = Decimal(item.get('precio_unitario', '0.00')) # Usamos costo como precio de salida
                
                # Usar select_for_update para prevenir condiciones de carrera al modificar el stock
                elemento = ElementoInventario.objects.select_for_update().get(pk=item['id_elemento'])
                
                stock_actual_decimal = Decimal(elemento.stock_actual) if elemento.stock_actual is not None else Decimal('0.00')

                # Re-validación de Stock (seguridad)
                if cantidad_db > stock_actual_decimal:
                    raise IntegrityError(f"Stock insuficiente para {elemento.descripcion}. Solo {stock_actual_decimal} disponibles.")

                # Crear el Movimiento de Inventario
                MovimientoInventario.objects.create(
                    elemento=elemento,
                    tipo='SALIDA',
                    cantidad=cantidad_db, 
                    precio_unitario=precio_unitario_db, 
                    fecha_movimiento=timezone.now(),
                    responsable=request.user,
                    referencia=item.get('destino_referencia', ''), 
                )

                # CORRECCIÓN CLAVE: Restamos la cantidad
                elemento.stock_actual = stock_actual_decimal - cantidad_db
                elemento.save()
            
            # Limpiar la sesión después de confirmar
            request.session.pop(SESSION_KEY, None)
            request.session.modified = True
            
            messages.success(request, f"Salidas registradas y confirmadas con éxito. {len(salidas_temporales)} ítems procesados.")
        
    except IntegrityError as e:
        messages.error(request, f"Error de Stock. Transacción revertida. Detalle: {e}")
    except Exception as e:
        messages.error(request, f"Error al confirmar las salidas. Transacción revertida. Detalle: {e}")
        
    return redirect('inventario:salidas')