from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('productos/', views.productos_list, name='productos_list'),
    path('productos/<int:product_id>/', views.producto_detail, name='producto_detail'),
    path('categorias/', views.categorias_list, name='categorias_list'),
]
