from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from tracks.models import Track
from .services import LicenseService
from .models import User


# @login_required
def licensing_view(request):
    if request.method == "POST":
        track_id = request.POST.get("track_id")
        license_type = request.POST.get("license_type", "basic")

        track = Track.objects.get(id=track_id)

    # USUARIO DE PRUEBA
        userLocal = User.objects.first()
        try:
            LicenseService.crear_licencia(
                user=userLocal, #ASUMIENDO QUE EL USUARIO ESTÁ AUTENTICADO
                track=track,
                license_type=license_type
            )
            return HttpResponse("Licencia creada")
        except ValueError as e:
            tracks = Track.objects.all()
            return render(
                request,
                "licensing.html",
                {
                    "error": str(e),
                    "tracks": tracks,
                }
            )

    # GET
    tracks = Track.objects.all()
    return render(
        request,
        "licensing.html",
        {"tracks": tracks}
    )

