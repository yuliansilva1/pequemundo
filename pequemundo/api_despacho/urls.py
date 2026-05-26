from django.urls import path
from . import views

app_name = 'api_despacho'

urlpatterns = [
    path('pedidos/<int:id_pedido>/', views.obtener_estado_pedido, name='obtener_estado_pedido'),
    
    path('pedidos/<int:id_pedido>/actualizar-estado/', views.actualizar_estado_pedido, name='actualizar_estado_pedido'),
]
