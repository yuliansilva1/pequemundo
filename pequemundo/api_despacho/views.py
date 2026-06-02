import json
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Asegúrate de importar correctamente el modelo Pedido según la estructura de tus apps
from pequemundo.models import Pedido 

@api_view(['GET'])
def prueba_debug(request):
    """
    Ruta de prueba básica para verificar que el módulo de despacho responde.
    """
    return Response(
        {'mensaje': 'Ruta de prueba de despacho funcionando correctamente'}, 
        status=status.HTTP_200_OK
    )

@api_view(['PUT', 'PATCH'])
def actualizar_estado_pedido(request, codigo):
    """
    Método: PUT o PATCH
    URL: /api_despacho/pedidos/{codigo}/actualizar-estado/
    
    Permite a la empresa de transporte externa avanzar el tracking logístico.
    """
    try:
        # Busca el pedido ignorando mayúsculas/minúsculas en el código único de seguimiento
        pedido = Pedido.objects.get(codigo__iexact=codigo)
    except Pedido.DoesNotExist:
        return Response(
            {'error': 'Pedido no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # REGLA DE NEGOCIO: Si el cliente seleccionó retirar en la tienda física de Santiago, [cite: 7, 74]
    # la empresa de transporte externa no tiene permitido intervenir mediante el servicio web[cite: 95].
    if pedido.tipo_entrega == 'Retiro en Tienda':
        return Response(
            {'error': 'No se puede actualizar vía API externa un pedido con modalidad Retiro en Tienda'},
            status=status.HTTP_400_BAD_REQUEST
        )

    nuevo_estado = request.data.get('estado')
    
    if not nuevo_estado:
        return Response(
            {'error': 'El campo "estado" es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # REGLA DE NEGOCIO RESTRICTIVA: La transportista externa SOLO puede declarar que el mueble
    # va en camino hacia el domicilio o que ya fue entregado a la familia[cite: 94].
    # Los estados internos de la empresa ("Pedido recibido" o "Pedido en preparación") quedan bloqueados.
    mapa_estados_externos = {
        'Pedido en camino': 'EN_CAMINO',
        'Pedido en Camino': 'EN_CAMINO',
        'En Camino': 'EN_CAMINO',
        'En Despacho': 'EN_CAMINO',
        'Pedido entregado': 'ENTREGADO',
        'Pedido Entregado': 'ENTREGADO',
        'Entregado': 'ENTREGADO',
        'EN_CAMINO': 'EN_CAMINO',
        'ENTREGADO': 'ENTREGADO'
    }
    
    if nuevo_estado not in mapa_estados_externos:
        estados_validos_mostrar = ['Pedido en camino', 'Pedido entregado']
        return Response(
            {
                'error': f'Estado inválido para despacho externo. La transportista solo puede reportar: {", ".join(estados_validos_mostrar)}',
                'estados_validos': estados_validos_mostrar
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Almacenamos el estado previo para retornarlo en la respuesta del JSON de éxito
    estado_anterior = pedido.estado
    
    # Actualización automática en la Base de Datos
    pedido.estado = mapa_estados_externos[nuevo_estado]
    pedido.save()
    
    # Mapeo para mostrar el estado nuevo de forma amigable en el JSON de respuesta
    nombres_amigables = {
        'EN_CAMINO': 'Pedido en camino',
        'ENTREGADO': 'Pedido entregado'
    }
    
    return Response(
        {
            'mensaje': 'Estado del pedido actualizado automáticamente por la empresa de transporte',
            'id_pedido': pedido.id_pedido,
            'estado_anterior': estado_anterior,
            'estado_nuevo': nombres_amigables.get(pedido.estado, nuevo_estado),
            'codigo_pedido': pedido.codigo,
            'total_final': str(pedido.total_final),
            'direccion_entrega': pedido.direccion_entrega
        },
        status=status.HTTP_200_OK
    )

@api_view(['GET'])
def obtener_estado_pedido(request, codigo):
    """
    Método: GET
    URL: /api_despacho/pedidos/{codigo}/
    
    Permite consultar los datos base del pedido y su estado de entrega.
    """
    try:
        pedido = Pedido.objects.get(codigo__iexact=codigo)
    except Pedido.DoesNotExist:
        return Response(
            {'error': 'Pedido no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Mapeo inverso para devolver el texto exacto exigido por el caso de estudio 
    estado_mostrar = {
        'RECIBIDO': 'Pedido recibido',
        'EN_PREPARACION': 'Pedido en preparación',
        'EN_CAMINO': 'Pedido en camino',
        'ENTREGADO': 'Pedido entregado',
        'CANCELADO': 'Pedido cancelado'
    }

    return Response(
        {
            'id_pedido': pedido.id_pedido,
            'codigo': pedido.codigo,
            'estado': estado_mostrar.get(pedido.estado, pedido.estado),
            'total_final': str(pedido.total_final),
            'fecha_pedido': pedido.fecha_pedido,
            'fecha_entrega': pedido.fecha_entrega,
            'direccion_entrega': pedido.direccion_entrega,
            'tipo_entrega': pedido.tipo_entrega,
            'region': pedido.region
        },
        status=status.HTTP_200_OK
    )