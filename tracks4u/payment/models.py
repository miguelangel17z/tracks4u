from django.db import models


class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("CARD", "Card"),
        ("PAYPAL", "PayPal"),
        ("PSE", "PSE"),
        ("OTHER", "Other"),
    ]
    STATUS_CHOICES = [
        ("PLACED", "Placed"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        db_column="user_id",
        related_name="orders",
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    payment_method = models.CharField(
        max_length=60,
        null=True,
        blank=True,
        choices=PAYMENT_METHOD_CHOICES,
    )
    status = models.CharField(
        max_length=30,
        default="PLACED",
        choices=STATUS_CHOICES,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "order"

    def __str__(self):
        return f"Order #{self.id} ({self.user}) - {self.status}"


class OrderItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column="order_id",
        related_name="items",
    )
    track = models.ForeignKey(
        "tracks.Track",
        on_delete=models.PROTECT,
        db_column="track_id",
        related_name="order_items",
    )
    price_paid = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "order_item"
        unique_together = [("order", "track")]

    def __str__(self):
        return f"OrderItem #{self.id} (Order #{self.order_id} - Track #{self.track_id})"
