from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Producto, Usuario, Categoria, Pedido, PedidoItem


def _get_cart(request):
    return request.session.get('cart', {})


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
    cart_count = sum(_get_cart(request).values())
    return render(request, 'catalogo.html', {'productos': productos_data, 'cart_count': cart_count})

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
                return redirect('/')
            messages.error(request, 'Credenciales inválidas')
        except Usuario.DoesNotExist:
            messages.error(request, 'Credenciales inválidas')
    return render(request, 'login.html')


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
            usuario = Usuario(
                nombre=nombre,
                apellido=apellido or None,
                email=email or None,
                contrasena=make_password(password),
                id_rol=1,
                activo='1',
                fecha_registro=timezone.now()
            )
            usuario.save()
            messages.success(request, 'Usuario creado correctamente. Inicia sesión para continuar.')
            return redirect('login')

    return render(request, 'register.html')


def logout_view(request):
    request.session.flush()
    return redirect('catalogo')


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

    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debes iniciar sesión para poder pagar el pedido.')
        return redirect('login')

    usuario = Usuario.objects.filter(id_usuario=user_id, activo='1').first()
    if not usuario:
        messages.error(request, 'Usuario inválido. Inicia sesión nuevamente.')
        return redirect('login')

    try:
        order_code = timezone.now().strftime('PM%Y%m%d%H%M%S')
        pedido = Pedido.objects.create(
            id_usuario=usuario,
            codigo=order_code,
            fecha_pedido=timezone.now(),
            total=total,
            costo_despacho=0,
            total_final=total,
            estado='EN_PREPARACION',
            tipo_entrega='RETIRO_TIENDA',
            direccion_entrega='Retiro en tienda',
            region='Santiago',
        )

        for item in cart_items:
            producto = Producto.objects.get(id_producto=item['id'])
            PedidoItem.objects.create(
                id_pedido=pedido,
                id_producto=producto,
                cantidad=item['cantidad'],
                precio_unitario=item['precio'],
                subtotal=item['subtotal'],
            )
            if producto.stock is not None:
                producto.stock = max(0, producto.stock - item['cantidad'])
                producto.save(update_fields=['stock'])

        request.session['cart'] = {}
        request.session.modified = True
        messages.success(request, 'Tu pedido fue confirmado correctamente.')
        return redirect('pedidos')

    except Exception as e:
        messages.error(request, f'Error al confirmar pedido: {e}')
        return redirect('pago')


def pedidos(request):
    pedidos_qs = Pedido.objects.prefetch_related('items__id_producto').order_by('-fecha_pedido')
    orders = []

    for pedido in pedidos_qs:
        items = []
        for item in pedido.items.all():
            items.append({
                'id': item.id_producto.id_producto,
                'nombre': item.id_producto.nombre,
                'cantidad': item.cantidad,
                'subtotal': float(item.subtotal),
                'precio': float(item.precio_unitario),
                'imagen_url': item.id_producto.imagen_url or _default_image_for_categoria(item.id_producto.id_categoria.nombre if item.id_producto.id_categoria else ''),
            })

        orders.append({
            'id': pedido.id_pedido,
            'date': pedido.fecha_pedido.strftime('%d de %B de %Y'),
            'total': float(pedido.total),
            'status': pedido.estado,
            'eta': '5-7 días hábiles',
            'items': items,
        })

    total_orders = len(orders)
    in_process = sum(1 for order in orders if order.get('status') != 'Entregado')
    completed = total_orders - in_process
    cart_count = sum(_get_cart(request).values())
    return render(request, 'pedidos.html', {
        'orders': orders,
        'total_orders': total_orders,
        'in_process': in_process,
        'completed': completed,
        'cart_count': cart_count,
    })