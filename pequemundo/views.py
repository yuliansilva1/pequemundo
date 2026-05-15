from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import models
from .models import Producto, Usuario, Categoria, Pedido, PedidoItem


def _get_cart(request):
    return request.session.get('cart', {})

DELIVERY_TYPE_MAP = {
    'Retiro en Tienda': 'RETIRO_TIENDA',
    'Despacho a Domicilio': 'DESPACHO_DOMICILIO',
    'RETIRO_TIENDA': 'RETIRO_TIENDA',
    'DESPACHO_DOMICILIO': 'DESPACHO_DOMICILIO',
}

ORDER_STATUS_MAP = {
    'Recibido': 'RECIBIDO',
    'En Preparación': 'EN_PREPARACION',
    'En Camino': 'EN_CAMINO',
    'Entregado': 'ENTREGADO',
    'Cancelado': 'CANCELADO',
    'RECIBIDO': 'RECIBIDO',
    'EN_PREPARACION': 'EN_PREPARACION',
    'EN_CAMINO': 'EN_CAMINO',
    'ENTREGADO': 'ENTREGADO',
    'CANCELADO': 'CANCELADO',
}

ORDER_STATUS_DISPLAY = {
    'RECIBIDO': 'Recibido',
    'EN_PREPARACION': 'En Preparación',
    'EN_CAMINO': 'En Camino',
    'ENTREGADO': 'Entregado',
    'CANCELADO': 'Cancelado',
}


def _normalize_delivery_type(delivery):
    return DELIVERY_TYPE_MAP.get(delivery, 'RETIRO_TIENDA')


def _normalize_order_status(status):
    return ORDER_STATUS_MAP.get(status, 'RECIBIDO')


def _format_order_status(status_key):
    return ORDER_STATUS_DISPLAY.get(status_key, ORDER_STATUS_DISPLAY['RECIBIDO'])


def _get_status_class(status_key):
    if status_key == 'EN_CAMINO':
        return 'status-camino'
    if status_key == 'ENTREGADO':
        return 'status-entregado'
    return 'status-prep'


def _migrate_session_orders_to_user(request, user):
    session_orders = request.session.get('orders', [])
    if not session_orders:
        return

    for order_data in session_orders:
        try:
            order_status = _normalize_order_status(order_data.get('status', 'Recibido'))
            order = Pedido(
                id_usuario=user,
                codigo=order_data.get('id'),
                estado=order_status,
                total=order_data.get('total') or 0,
                total_final=order_data.get('total') or 0,
                costo_despacho=0,
                fecha_pedido=timezone.now(),
            )
            order.save()

            for item_data in order_data.get('items', []):
                producto = Producto.objects.filter(id_producto=item_data.get('id')).first()
                if not producto:
                    continue
                PedidoItem.objects.create(
                    id_pedido=order,
                    id_producto=producto,
                    cantidad=item_data.get('cantidad', 0),
                    precio_unitario=item_data.get('precio') or 0,
                    subtotal=item_data.get('subtotal') or 0,
                )
        except Exception:
            continue

    request.session.pop('orders', None)
    request.session.modified = True


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _default_image_for_categoria(categoria):
    lower = categoria.lower() if categoria else ''
    if lower == 'camas':
        return 'https://bainba.com/14428-thickbox_default/cama-para-ninos-montessori-nube.jpg'
    if lower == 'cunas':
        return 'https://blasibed.com/wp-content/uploads/2023/04/cuna-estela-300x300.jpg'
    if lower == 'escritorios':
        return 'https://i.etsystatic.com/23154329/r/il/7f551e/6694723444/il_794xN.6694723444_aqro.jpg'
    return f'https://via.placeholder.com/300x180?text={categoria or "Producto"}'


def _get_cart_items(request):
    cart = _get_cart(request)
    items = []
    total = 0
    for product_id, qty in cart.items():
        try:
            producto = Producto.objects.get(id_producto=int(product_id), activo__in=['1', None])
            item_total = float(producto.precio) * qty
            total += item_total
            items.append({
                'id': producto.id_producto,
                'nombre': producto.nombre,
                'precio': float(producto.precio),
                'cantidad': qty,
                'subtotal': item_total,
                'imagen_url': producto.imagen_url or _default_image_for_categoria(producto.id_categoria.nombre if producto.id_categoria else ''),
            })
        except Producto.DoesNotExist:
            continue
    return items, total


def catalogo(request):
    try:
        productos = Producto.objects.select_related('id_categoria').filter(activo__in=['1', None])
        productos_data = [
            {
                'id': p.id_producto,
                'nombre': p.nombre,
                'precio': float(p.precio),
                'stock': p.stock,
                'categoria': p.id_categoria.nombre if p.id_categoria else 'Sin categoria',
                'imagen_url': p.imagen_url if getattr(p, 'imagen_url', None) else ''
            } for p in productos
        ]
    except Exception as e:
        productos_data = []
        print(f"Error en catalogo: {e}")
    
    # Verificar si el usuario es administrador
    is_admin = False
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = Usuario.objects.get(id_usuario=user_id)
            is_admin = user.id_rol == 1
        except Usuario.DoesNotExist:
            pass
    
    cart_count = sum(_get_cart(request).values())
    return render(request, 'catalogo.html', {
        'productos': productos_data, 
        'cart_count': cart_count,
        'is_admin': is_admin
    })

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = Usuario.objects.get(nombre=username, activo='1')
            valid_password = False
            if user.contrasena:
                valid_password = check_password(password, user.contrasena)
                if not valid_password:
                    valid_password = password == user.contrasena
            if valid_password:
                request.session['user_id'] = user.id_usuario
                request.session['username'] = user.nombre
                request.session['user_role'] = user.id_rol
                _migrate_session_orders_to_user(request, user)
                
                # Redirigir según el rol del usuario
                if user.id_rol == 1:  # ADMIN
                    return redirect('admin_dashboard')
                else:
                    return redirect('/')
            messages.error(request, 'Credenciales inválidas')
        except Usuario.DoesNotExist:
            messages.error(request, 'Credenciales inválidas')
    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        if not nombre or not password:
            messages.error(request, 'El nombre de usuario y la contraseña son obligatorios.')
        elif password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden.')
        elif Usuario.objects.filter(nombre=nombre).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
        else:
            # Todos los nuevos usuarios se registran como CLIENTE (rol 4)
            usuario = Usuario(
                nombre=nombre,
                apellido=apellido or None,
                email=email or None,
                contrasena=make_password(password),
                id_rol=4,  # CLIENTE por defecto
                activo='1',
                fecha_registro=timezone.now()
            )
            usuario.save()
            messages.success(request, 'Usuario creado correctamente. Inicia sesión para continuar.')
            return redirect('login')

    return render(request, 'register.html')


def user_profile(request):
    """Vista de perfil del usuario"""
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debes iniciar sesión.')
        return redirect('login')
    
    try:
        usuario = Usuario.objects.get(id_usuario=user_id)
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('login')
    
    if request.method == 'POST':
        apellido = request.POST.get('apellido', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        imagen_url = request.POST.get('imagen_url', '').strip()
        
        usuario.apellido = apellido or None
        usuario.email = email or None
        usuario.telefono = telefono or None
        usuario.direccion = direccion or None
        usuario.imagen_url = imagen_url or None
        usuario.save()
        
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('user_profile')
    
    # Obtener historial de compras
    pedidos = Pedido.objects.filter(id_usuario=usuario).order_by('-fecha_pedido')
    pedidos_data = []
    for pedido in pedidos:
        items = []
        for item in pedido.items.select_related('id_producto').all():
            items.append({
                'nombre': item.id_producto.nombre if item.id_producto else 'Producto',
                'cantidad': item.cantidad,
                'precio': float(item.precio_unitario or 0),
            })
        pedidos_data.append({
            'id': pedido.id_pedido,
            'codigo': pedido.codigo,
            'estado': pedido.estado,
            'total': float(pedido.total_final or 0),
            'fecha': pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M') if pedido.fecha_pedido else '',
            'items': items,
        })
    
    cart_count = sum(_get_cart(request).values())
    
    return render(request, 'user_profile.html', {
        'usuario': usuario,
        'pedidos': pedidos_data,
        'cart_count': cart_count,
    })


def user_edit_profile(request):
    """Vista para editar perfil del usuario"""
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debes iniciar sesión.')
        return redirect('login')
    
    try:
        usuario = Usuario.objects.get(id_usuario=user_id)
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('login')
    
    if request.method == 'POST':
        apellido = request.POST.get('apellido', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        imagen_url = request.POST.get('imagen_url', '').strip()
        
        usuario.apellido = apellido or None
        usuario.email = email or None
        usuario.telefono = telefono or None
        usuario.direccion = direccion or None
        usuario.imagen_url = imagen_url or None
        usuario.save()
        
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('user_profile')
    
    cart_count = sum(_get_cart(request).values())
    
    return render(request, 'user_edit_profile.html', {
        'usuario': usuario,
        'cart_count': cart_count,
    })


def add_product(request):
    if not request.session.get('username'):
        messages.error(request, 'Debes iniciar sesión para agregar productos.')
        return redirect('login')

    categorias = Categoria.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '0').strip()
        stock = request.POST.get('stock', '0').strip()
        categoria_id = request.POST.get('categoria')
        descripcion = request.POST.get('descripcion', '').strip()
        imagen_url = request.POST.get('imagen_url', '').strip()

        if not nombre:
            messages.error(request, 'El nombre del producto es obligatorio.')
        else:
            try:
                categoria = Categoria.objects.get(id_categoria=categoria_id) if categoria_id else None
                producto = Producto(
                    nombre=nombre,
                    precio=precio,
                    stock=int(stock),
                    id_categoria=categoria,
                    descripcion=descripcion,
                    imagen_url=imagen_url,
                    activo='1',
                    fecha_creacion=timezone.now()
                )
                producto.save()
                messages.success(request, 'Producto agregado correctamente.')
                return redirect('catalogo')
            except Exception as e:
                messages.error(request, f'Error al agregar el producto: {e}')

    return render(request, 'add_product.html', {'categorias': categorias})


def edit_product(request, product_id):
    if not request.session.get('username'):
        messages.error(request, 'Debes iniciar sesión para editar productos.')
        return redirect('login')

    try:
        producto = Producto.objects.get(id_producto=product_id)
    except Producto.DoesNotExist:
        messages.error(request, 'Producto no encontrado.')
        return redirect('catalogo')

    categorias = Categoria.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '0').strip()
        stock = request.POST.get('stock', '0').strip()
        categoria_id = request.POST.get('categoria')
        activo = request.POST.get('activo', '1')

        if not nombre:
            messages.error(request, 'El nombre del producto es obligatorio.')
        else:
            try:
                producto.nombre = nombre
                producto.precio = precio
                producto.stock = int(stock)
                producto.activo = activo
                producto.imagen_url = request.POST.get('imagen_url', '').strip()
                if categoria_id:
                    producto.id_categoria = Categoria.objects.get(id_categoria=categoria_id)
                producto.save()
                messages.success(request, 'Producto actualizado correctamente.')
                return redirect('catalogo')
            except Exception as e:
                messages.error(request, f'Error al actualizar el producto: {e}')

    return render(request, 'edit_product.html', {
        'producto': producto,
        'categorias': categorias,
    })

@require_POST
def add_to_cart(request, product_id):
    try:
        producto = Producto.objects.get(id_producto=product_id, activo__in=['1', None])
    except Producto.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Producto no encontrado.'}, status=404)

    cart = _get_cart(request)
    product_key = str(product_id)
    quantity = cart.get(product_key, 0) + 1

    if producto.stock is not None and quantity > producto.stock:
        return JsonResponse({'success': False, 'message': 'Stock insuficiente.'}, status=400)

    cart[product_key] = quantity
    _save_cart(request, cart)

    return JsonResponse({'success': True, 'cart_count': sum(cart.values())})


def pago(request):
    cart_items, total = _get_cart_items(request)
    cart_count = sum(_get_cart(request).values())
    return render(request, 'pago.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
    })

@require_POST
def checkout(request):
    cart_items, total = _get_cart_items(request)
    if not cart_items:
        messages.error(request, 'Tu carrito está vacío.')
        return redirect('pago')

    delivery = request.POST.get('delivery', 'Retiro en Tienda')
    delivery_type = _normalize_delivery_type(delivery)
    direccion = request.POST.get('direccion', '').strip() or 'Retiro en Tienda'
    region = request.POST.get('region', '').strip() or 'Región Metropolitana'

    user = None
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = Usuario.objects.get(id_usuario=user_id)
        except Usuario.DoesNotExist:
            user = None

    if user:
        order = Pedido(
            id_usuario=user,
            codigo=timezone.now().strftime('PM%Y%m%d%H%M%S'),
            estado=_normalize_order_status('En Preparación'),
            tipo_entrega=delivery_type,
            total=total,
            total_final=total,
            costo_despacho=0,
            region=region,
            direccion_entrega=direccion,
            fecha_pedido=timezone.now(),
        )
        order.save()

        for item in cart_items:
            producto = Producto.objects.filter(id_producto=item['id']).first()
            if not producto:
                continue
            PedidoItem.objects.create(
                id_pedido=order,
                id_producto=producto,
                cantidad=item['cantidad'],
                precio_unitario=item['precio'],
                subtotal=item['subtotal'],
            )
    else:
        orders = request.session.get('orders', [])
        order_id = timezone.now().strftime('PM%Y%m%d%H%M%S')
        order_date = timezone.now().strftime('%d de %B de %Y')

        orders.append({
            'id': order_id,
            'date': order_date,
            'total': total,
            'status': 'En Preparación',
            'eta': '5-7 días hábiles',
            'delivery': delivery,
            'items': cart_items,
        })
        request.session['orders'] = orders

    request.session['cart'] = {}
    request.session.modified = True

    messages.success(request, 'Tu pedido fue confirmado correctamente.')
    return redirect('pedidos')


def pedidos(request):
    orders = []
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = Usuario.objects.get(id_usuario=user_id)
            pedidos_qs = Pedido.objects.filter(id_usuario=user).order_by('-fecha_pedido')
            for pedido_obj in pedidos_qs:
                items = []
                for item in pedido_obj.items.select_related('id_producto').all():
                    producto = item.id_producto
                    items.append({
                        'id': producto.id_producto if producto else None,
                        'nombre': producto.nombre if producto else '',
                        'precio': float(item.precio_unitario or 0),
                        'cantidad': item.cantidad,
                        'subtotal': float(item.subtotal or 0),
                        'imagen_url': producto.imagen_url if producto and producto.imagen_url else _default_image_for_categoria(producto.id_categoria.nombre if producto and producto.id_categoria else ''),
                    })
                status_key = _normalize_order_status(pedido_obj.estado or 'RECIBIDO')
                orders.append({
                    'id': pedido_obj.codigo or f'PM{pedido_obj.id_pedido}',
                    'date': pedido_obj.fecha_pedido.strftime('%d de %B de %Y') if pedido_obj.fecha_pedido else '',
                    'total': float(pedido_obj.total or 0),
                    'status': _format_order_status(status_key),
                    'status_key': status_key,
                    'status_class': _get_status_class(status_key),
                    'eta': '5-7 días hábiles',
                    'items': items,
                })
        except Usuario.DoesNotExist:
            orders = request.session.get('orders', [])
    else:
        orders = request.session.get('orders', [])
        for order in orders:
            status_key = _normalize_order_status(order.get('status', 'En Preparación'))
            order['status'] = _format_order_status(status_key)
            order['status_key'] = status_key
            order['status_class'] = _get_status_class(status_key)

    total_orders = len(orders)
    in_process = sum(1 for order in orders if order.get('status_key') != 'ENTREGADO')
    completed = total_orders - in_process
    cart_count = sum(_get_cart(request).values())
    return render(request, 'pedidos.html', {
        'orders': orders,
        'total_orders': total_orders,
        'in_process': in_process,
        'completed': completed,
        'cart_count': cart_count,
    })


def admin_dashboard(request):
    """Panel de administrador con estadísticas y gestión general"""
    # Verificar si el usuario es administrador
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debes iniciar sesión.')
        return redirect('login')
    
    try:
        user = Usuario.objects.get(id_usuario=user_id)
        if user.id_rol != 1:  # Solo administradores
            messages.error(request, 'No tienes permiso para acceder.')
            return redirect('catalogo')
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('login')
    
    # Obtener estadísticas
    total_usuarios = Usuario.objects.count()
    usuarios_activos = Usuario.objects.filter(activo='1').count()
    
    # Contar usuarios por rol
    roles_count = {
        'ADMIN': Usuario.objects.filter(id_rol=1).count(),
        'VENDEDOR': Usuario.objects.filter(id_rol=2).count(),
        'FINANZAS': Usuario.objects.filter(id_rol=3).count(),
        'CLIENTE': Usuario.objects.filter(id_rol=4).count(),
        'DESPACHO': Usuario.objects.filter(id_rol=5).count(),
    }
    
    # Obtener últimos pedidos
    ultimos_pedidos = Pedido.objects.select_related('id_usuario').order_by('-fecha_pedido')[:10]
    pedidos_data = []
    for pedido in ultimos_pedidos:
        pedidos_data.append({
            'id': pedido.id_pedido,
            'codigo': pedido.codigo,
            'usuario': pedido.id_usuario.nombre if pedido.id_usuario else 'Anónimo',
            'estado': pedido.estado,
            'total': float(pedido.total_final or 0),
            'fecha': pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M') if pedido.fecha_pedido else '',
        })
    
    # Contar pedidos por estado
    pedidos_por_estado = {
        'RECIBIDO': Pedido.objects.filter(estado='RECIBIDO').count(),
        'EN_PREPARACION': Pedido.objects.filter(estado='EN_PREPARACION').count(),
        'EN_CAMINO': Pedido.objects.filter(estado='EN_CAMINO').count(),
        'ENTREGADO': Pedido.objects.filter(estado='ENTREGADO').count(),
        'CANCELADO': Pedido.objects.filter(estado='CANCELADO').count(),
    }
    
    total_pedidos = Pedido.objects.count()
    
    # Obtener últimos usuarios registrados
    ultimos_usuarios = Usuario.objects.order_by('-fecha_registro')[:5]
    usuarios_data = []
    roles_map = {1: 'ADMIN', 2: 'VENDEDOR', 3: 'FINANZAS', 4: 'CLIENTE', 5: 'DESPACHO'}
    for usuario in ultimos_usuarios:
        usuarios_data.append({
            'id': usuario.id_usuario,
            'nombre': usuario.nombre,
            'email': usuario.email or 'N/A',
            'rol': roles_map.get(usuario.id_rol or 4, 'CLIENTE'),
            'fecha_registro': usuario.fecha_registro.strftime('%d/%m/%Y') if usuario.fecha_registro else '',
        })
    
    # Calcular total de ventas
    total_ventas = Pedido.objects.aggregate(total=models.Sum('total_final'))['total'] or 0
    
    cart_count = sum(_get_cart(request).values())
    
    return render(request, 'admin_dashboard.html', {
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'roles_count': roles_count,
        'ultimos_pedidos': pedidos_data,
        'pedidos_por_estado': pedidos_por_estado,
        'total_pedidos': total_pedidos,
        'ultimos_usuarios': usuarios_data,
        'total_ventas': float(total_ventas),
        'cart_count': cart_count,
    })


def manage_users(request):
    # Verificar si el usuario es administrador (id_rol = 1 es admin)
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debes iniciar sesión para acceder a este panel.')
        return redirect('login')
    
    try:
        user = Usuario.objects.get(id_usuario=user_id)
        # Verificar si es administrador (id_rol = 1)
        if user.id_rol != 1:
            messages.error(request, 'No tienes permiso para acceder a este panel.')
            return redirect('catalogo')
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('login')
    
    # Obtener todos los usuarios
    usuarios = Usuario.objects.all().order_by('nombre')
    
    # Mapeo de roles
    roles_map = {
        1: 'ADMIN',
        2: 'VENDEDOR',
        3: 'FINANZAS',
        4: 'CLIENTE',
        5: 'DESPACHO',
    }
    
    usuarios_data = []
    for usuario in usuarios:
        usuarios_data.append({
            'id': usuario.id_usuario,
            'nombre': usuario.nombre,
            'apellido': usuario.apellido or '',
            'email': usuario.email or '',
            'telefono': usuario.telefono or '',
            'id_rol': usuario.id_rol or 4,
            'rol_actual': roles_map.get(usuario.id_rol or 4, 'CLIENTE'),
            'activo': usuario.activo,
            'fecha_registro': usuario.fecha_registro.strftime('%d/%m/%Y') if usuario.fecha_registro else '',
        })
    
    cart_count = sum(_get_cart(request).values())
    
    return render(request, 'manage_users.html', {
        'usuarios': usuarios_data,
        'roles': roles_map,
        'cart_count': cart_count,
    })


@require_POST
def update_user_role(request, user_id):
    # Verificar si el usuario es administrador
    admin_user_id = request.session.get('user_id')
    if not admin_user_id:
        return JsonResponse({'success': False, 'message': 'No autenticado'}, status=401)
    
    try:
        admin_user = Usuario.objects.get(id_usuario=admin_user_id)
        if admin_user.id_rol != 1:  # Solo administradores
            return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
    except Usuario.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Admin no encontrado'}, status=401)
    
    try:
        usuario = Usuario.objects.get(id_usuario=user_id)
        new_role = request.POST.get('rol')
        
        if new_role not in ['1', '2', '3', '4', '5']:
            return JsonResponse({'success': False, 'message': 'Rol inválido'}, status=400)
        
        usuario.id_rol = int(new_role)
        usuario.save()
        
        roles_map = {1: 'ADMIN', 2: 'VENDEDOR', 3: 'FINANZAS', 4: 'CLIENTE', 5: 'DESPACHO'}
        return JsonResponse({
            'success': True,
            'message': f'Rol actualizado a {roles_map.get(int(new_role))}',
            'new_role': roles_map.get(int(new_role))
        })
    except Usuario.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)