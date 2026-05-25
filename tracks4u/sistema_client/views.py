from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from .services.client import SistemaAPIClient


from django.shortcuts import render

def estado_page(request):
    return render(request, "sistema_client/estado.html")


def estado_sistema(request):
    client = SistemaAPIClient()
    data = client.get_estado_sistema()
    return JsonResponse(data, safe=False)