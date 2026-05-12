from django.http import JsonResponse
from ..models import Producto, Categoria


def productos_list(request):
    productos = Producto.objects.select_related('id_categoria').filter(activo__in=['1', None])
    productos_data = [
        {
            'id': producto.id_producto,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'stock': producto.stock,
            'categoria': producto.id_categoria.nombre if producto.id_categoria else None,
            'imagen_url': producto.imagen_url or '',
            'activo': producto.activo,
        }
        for producto in productos
    ]
    return JsonResponse({'productos': productos_data}, safe=False)


def producto_detail(request, product_id):
    try:
        producto = Producto.objects.select_related('id_categoria').get(id_producto=product_id, activo__in=['1', None])
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    data = {
        'id': producto.id_producto,
        'nombre': producto.nombre,
        'precio': float(producto.precio),
        'stock': producto.stock,
        'categoria': producto.id_categoria.nombre if producto.id_categoria else None,
        'imagen_url': producto.imagen_url or '',
        'descripcion': producto.descripcion or '',
        'activo': producto.activo,
    }
    return JsonResponse(data)


def categorias_list(request):
    categorias = Categoria.objects.filter(activo__in=['1', None])
    categorias_data = [
        {
            'id': categoria.id_categoria,
            'nombre': categoria.nombre,
            'descripcion': categoria.descripcion or '',
        }
        for categoria in categorias
    ]
    return JsonResponse({'categorias': categorias_data}, safe=False)
