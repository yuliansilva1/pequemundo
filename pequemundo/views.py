from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from .models import Producto, Usuario, Categoria

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
    return render(request, 'catalogo.html', {'productos': productos_data})

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

def pago(request):
    return render(request, 'pago.html')

def pedidos(request):
    return render(request, 'pedidos.html')