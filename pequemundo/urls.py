"""
URL configuration for pequemundo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('pequemundo.api.urls')),
    path('', views.catalogo, name='catalogo'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('pedidos/', views.pedidos, name='pedidos'),
    path('pago/', views.pago, name='pago'),
    path('checkout/', views.checkout, name='checkout'),
    path('agregar-carrito/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('producto/nuevo/', views.add_product, name='add_product'),
    path('producto/<int:product_id>/editar/', views.edit_product, name='edit_product'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.user_profile, name='user_profile'),
    path('perfil/editar/', views.user_edit_profile, name='user_edit_profile'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/usuarios/', views.manage_users, name='manage_users'),
    path('admin-panel/usuarios/<int:user_id>/role/', views.update_user_role, name='update_user_role'),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
