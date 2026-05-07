from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

def catalogo(request):
    return render(request, 'catalogo.html')

def pago(request):
    return render(request, 'pago.html')

def pedidos(request):
    return render(request, 'pedidos.html')