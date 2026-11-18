from decimal import Decimal
from typing import List

from payment.models import Order, OrderItem
from tracks.models import Track
from users.models import User


class OrderBuilder:
    """Constructor fluido con validación acumulada para órdenes de compra de tracks."""

    def __init__(self):
        self.user = None
        self.tracks: List[Track] = []
        self.payment_method = None
        self.currency = "USD"
        self.errores: List[str] = []

    def para_user(self, user: User):
        self.user = user
        return self

    def agregar_track(self, track: Track):
        self.tracks.append(track)
        return self

    def para_tracks(self, tracks: List[Track]):
        for track in tracks:
            self.agregar_track(track)
        return self

    def con_pago(self, payment_method: str, currency: str = "USD"):
        self.payment_method = payment_method
        self.currency = currency or "USD"
        return self

    def validar(self):
        self.errores = []

        if self.user is None:
            self.errores.append("User is required.")
        elif not isinstance(self.user, User):
            self.errores.append("Invalid user.")

        if not self.tracks:
            self.errores.append("At least one track is required.")
        elif len(self.tracks) > 50:
            self.errores.append("An order cannot contain more than 50 tracks.")

        valid_payment_methods = dict(Order.PAYMENT_METHOD_CHOICES)
        if not self.payment_method:
            self.errores.append("Payment method is required.")
        elif self.payment_method not in valid_payment_methods:
            self.errores.append(f"Invalid payment method: {self.payment_method}.")

        seen_track_ids = set()
        valid_tracks: List[Track] = []
        for track in self.tracks:
            if not isinstance(track, Track) or track.id is None:
                self.errores.append("Invalid track in order.")
                continue
            if track.id in seen_track_ids:
                self.errores.append(f"Duplicate track in order: {track.title} (id={track.id}).")
            seen_track_ids.add(track.id)
            valid_tracks.append(track)

        if isinstance(self.user, User) and self.user.id is not None and valid_tracks:
            for track in valid_tracks:
                artist = getattr(track, "artist", None)
                if artist is not None and artist.user_id == self.user.id:
                    self.errores.append(
                        f"Artist cannot purchase their own track: {track.title}."
                    )

            already_owned = set(
                OrderItem.objects.filter(
                    order__user=self.user,
                    order__status="COMPLETED",
                    track_id__in=[t.id for t in valid_tracks],
                ).values_list("track_id", flat=True)
            )
            for track in valid_tracks:
                if track.id in already_owned:
                    self.errores.append(
                        f"You already own track: {track.title} (id={track.id})."
                    )

        return self

    def construir(self) -> dict:
        self.validar()
        if self.errores:
            raise ValueError("; ".join(self.errores))

        total_amount = sum((Decimal(str(t.price or 0)) for t in self.tracks), Decimal("0.00"))
        return {
            "user": self.user,
            "tracks": list(self.tracks),
            "payment_method": self.payment_method,
            "currency": self.currency,
            "total_amount": total_amount,
        }
