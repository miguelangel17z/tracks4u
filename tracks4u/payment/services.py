import logging
from typing import List, Optional

from django.conf import settings
from django.db import transaction

from payment.domain.builders import OrderBuilder
from payment.models import Order, OrderItem
from tracks.models import Track
from users.models import User

logger = logging.getLogger(__name__)


class OrderService:
    """Servicio transaccional para creación y consulta de órdenes de compra directa."""

    @staticmethod
    def crear_orden(
        user: User,
        track_ids: List[int],
        payment_method: str,
        currency: str = "USD",
    ) -> Order:
        if not track_ids:
            raise ValueError("At least one track_id is required.")

        with transaction.atomic():
            tracks_by_id = {
                t.id: t
                for t in Track.objects.filter(id__in=track_ids).select_related("artist")
            }
            missing = [tid for tid in set(track_ids) if tid not in tracks_by_id]
            if missing:
                raise ValueError(f"Tracks not found: {sorted(missing)}")

            ordered_tracks = [tracks_by_id[tid] for tid in track_ids]

            order_data = (
                OrderBuilder()
                .para_user(user)
                .para_tracks(ordered_tracks)
                .con_pago(payment_method=payment_method, currency=currency)
                .construir()
            )

            order = Order.objects.create(
                user=order_data["user"],
                total_amount=order_data["total_amount"],
                currency=order_data["currency"],
                payment_method=order_data["payment_method"],
                status="PLACED",
            )

            for track in order_data["tracks"]:
                OrderItem.objects.create(
                    order=order,
                    track=track,
                    price_paid=track.price,
                    currency=order_data["currency"],
                )

            # Pago simulado: pasa a COMPLETED en la misma transacción
            order.status = "COMPLETED"
            order.save(update_fields=["status", "updated_at"])

            transaction.on_commit(
                lambda: OrderService._notificar_orden_completada(order)
            )

            return order

    @staticmethod
    def _notificar_orden_completada(order: Order) -> None:
        """Encola la notificación de orden completada en Celery con fallback síncrono."""
        items_qs = OrderItem.objects.filter(order=order).select_related("track")
        item_titles = [item.track.title for item in items_qs]
        created_str = (
            order.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if order.created_at
            else ""
        )
        contexto = {
            "order_id": order.id,
            "user_username": order.user.username,
            "items": ", ".join(item_titles),
            "total_amount": str(order.total_amount),
            "currency": order.currency,
            "created_at": created_str,
        }
        destinatario = getattr(order.user, "email", None) or settings.ADMIN_EMAIL

        try:
            from tracks.infra.notifications.tasks import send_email_task

            send_email_task.delay(
                template_type="order_completed",
                destinatario=destinatario,
                contexto=contexto,
            )
        except Exception as exc:
            logger.warning(
                "Fallo al encolar notificación Celery para orden %s (%s); usando fallback síncrono.",
                order.id,
                exc,
            )
            try:
                from tracks.infra.notifications.factory import NotificationFactory

                notificador = NotificationFactory.crear_notificador(
                    tipo="email",
                    template_type="order_completed",
                )
                notificador.enviar(destinatario=destinatario, contexto=contexto)
            except Exception as inner:
                logger.error(
                    "No se pudo enviar notificación para la orden %s: %s",
                    order.id,
                    inner,
                )

    @staticmethod
    def obtener_compras_usuario(user: User) -> List[OrderItem]:
        return list(
            OrderItem.objects.filter(order__user=user, order__status="COMPLETED")
            .select_related("order", "track", "track__artist")
            .prefetch_related("track__genres")
            .order_by("-created_at")
        )

    @staticmethod
    def obtener_orden_usuario(user: User, order_id: int) -> Optional[Order]:
        return (
            Order.objects.filter(id=order_id, user=user)
            .prefetch_related("items__track__artist")
            .first()
        )
