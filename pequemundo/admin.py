from django.contrib import admin
from .models import Producto, Categoria

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id_categoria', 'nombre')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id_producto', 'nombre', 'categoria', 'precio', 'stock')
    list_filter = ('id_categoria',)

    def categoria(self, obj):
        return obj.id_categoria.nombre
    categoria.short_description = 'Categoría'