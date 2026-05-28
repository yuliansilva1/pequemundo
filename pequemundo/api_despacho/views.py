from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from pequemundo.models import Pedido
from django.views.decorators.http import require_http_methods
import json

@api_view(['GET'])
def prueba_debug(request):
    return Response({'mensaje': 'Ruta de prueba de despacho funcionando correctamente'}, status=status.HTTP_200_OK)

@api_view(['PUT', 'PATCH'])
def actualizar_estado_pedido(request, codigo):
    
    
    #Método: PUT o PATCH
    #URL: /api_despacho/pedidos/{codigo}/actualizar-estado/
    
    #Body JSON:
    #{
    #    "estado": "En Despacho"
    #}
    
    #Estados válidos:
    #- En Preparación
    #- En Despacho
    #- Entregado
    #- Cancelado
    
    try:
        pedido = Pedido.objects.get(codigo__iexact=codigo)
    except Pedido.DoesNotExist:
        return Response(
            {'error': 'Pedido no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    nuevo_estado = request.data.get('estado')
    
    if not nuevo_estado:
        return Response(
            {'error': 'El campo "estado" es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    
    # Mapeo de estados enviados por la API a los estados reales de la Base de Datos
    mapa_estados = {
        'En Preparación': 'EN_PREPARACION',
        'En Despacho': 'EN_CAMINO',
        'En Camino': 'EN_CAMINO',
        'Entregado': 'ENTREGADO',
        'Cancelado': 'CANCELADO',
        'EN_PREPARACION': 'EN_PREPARACION',
        'EN_CAMINO': 'EN_CAMINO',
        'ENTREGADO': 'ENTREGADO',
        'CANCELADO': 'CANCELADO'
    }
    
    if nuevo_estado not in mapa_estados:
        estados_validos_mostrar = ['En Preparación', 'En Despacho', 'Entregado', 'Cancelado']
        return Response(
            {
                'error': f'Estado inválido. Estados válidos: {", ".join(estados_validos_mostrar)}',
                'estados_validos': estados_validos_mostrar
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    estado_anterior = pedido.estado
    pedido.estado = mapa_estados[nuevo_estado]
    pedido.save()
    
    return Response(
        {
            'mensaje': 'Estado del pedido actualizado correctamente',
            'id_pedido': pedido.id_pedido,
            'estado_anterior': estado_anterior,
            'estado_nuevo': nuevo_estado,
            'codigo_pedido': pedido.codigo,
            'total_final': str(pedido.total_final),
            'direccion_entrega': pedido.direccion_entrega
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
def obtener_estado_pedido(request, codigo):
    try:
        pedido = Pedido.objects.get(codigo__iexact=codigo)
    except Pedido.DoesNotExist:
        return Response(
            {'error': 'Pedido no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Mapeo inverso para mostrar un estado amigable cuando se consulta (GET)
    estado_mostrar = {
        'RECIBIDO': 'Recibido',
        'EN_PREPARACION': 'En Preparación',
        'EN_CAMINO': 'En Despacho',
        'ENTREGADO': 'Entregado',
        'CANCELADO': 'Cancelado'
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
