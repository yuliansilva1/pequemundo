from django.urls import path
from . import views

app_name = 'api_despacho'

urlpatterns = [
    # Cambia <int:id_pedido> por <str:codigo>
    path('pedidos/<str:codigo>/', views.obtener_estado_pedido, name='obtener_estado_pedido'),
    path('pedidos/<str:codigo>/actualizar-estado/', views.actualizar_estado_pedido, name='actualizar_estado_pedido'),
    
    
    
]
