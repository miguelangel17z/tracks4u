from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from payment.api.serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    PurchaseSerializer,
)
from payment.services import OrderService


class OrderCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = OrderService.crear_orden(
                user=request.user,
                track_ids=serializer.validated_data["track_ids"],
                payment_method=serializer.validated_data["payment_method"],
            )
            return Response(
                OrderSerializer(order, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        order = OrderService.obtener_orden_usuario(request.user, pk)
        if order is None:
            return Response(
                {"error": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class MyPurchasesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        purchases = OrderService.obtener_compras_usuario(request.user)
        serializer = PurchaseSerializer(
            purchases,
            many=True,
            context={"request": request},
        )
        return Response(
            {"count": len(purchases), "results": serializer.data},
            status=status.HTTP_200_OK,
        )
