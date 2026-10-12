from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from .models import DeliveryOrder, OrderReview, UserProfile
from .serializers import (DeliveryOrderSerializer, LoginSerializer, OrderReviewSerializer,
                          RegisterSerializer, UserSerializer)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class DeliveryOrderViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryOrderSerializer

    def get_queryset(self):
        user = self.request.user
        role = getattr(getattr(user, "profile", None), "role", "student")
        if role == "admin":
            return DeliveryOrder.objects.select_related("requester", "courier").all()
        if role == "courier":
            return DeliveryOrder.objects.select_related("requester", "courier").filter(
                courier=user) | DeliveryOrder.objects.select_related("requester", "courier").filter(status="pending")
        return DeliveryOrder.objects.select_related("requester", "courier").filter(requester=user)

    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        order = self.get_object()
        role = getattr(getattr(request.user, "profile", None), "role", "student")
        if role != "courier":
            return Response({"detail": "只有配送员可以接单"}, status=403)
        if order.status != "pending":
            return Response({"detail": "该订单已被接单或不可接单"}, status=400)
        order.courier = request.user
        order.status = "accepted"
        order.accepted_at = timezone.now()
        order.save(update_fields=["courier", "status", "accepted_at", "updated_at"])
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get("status")
        allowed = {
            "accepted": {"picking", "cancelled"}, "picking": {"delivering", "cancelled"},
            "delivering": {"completed"}, "pending": {"cancelled"},
        }
        role = getattr(getattr(request.user, "profile", None), "role", "student")
        if request.user != order.courier and role != "admin" and not (request.user == order.requester and new_status == "cancelled"):
            return Response({"detail": "没有权限修改该订单"}, status=403)
        if new_status not in allowed.get(order.status, set()) and role != "admin":
            return Response({"detail": "不允许的订单状态流转"}, status=400)
        order.status = new_status
        if new_status == "completed":
            order.completed_at = timezone.now()
        order.save(update_fields=["status", "completed_at", "updated_at"])
        return Response(self.get_serializer(order).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        role = getattr(getattr(request.user, "profile", None), "role", "student")
        qs = self.get_queryset()
        data = {"total": qs.count(), "pending": qs.filter(status="pending").count(),
                "delivering": qs.filter(status__in=["accepted", "picking", "delivering"]).count(),
                "completed": qs.filter(status="completed").count(),
                "total_fee": str(qs.filter(status="completed").aggregate(total=Sum("fee"))["total"] or 0)}
        if role == "admin":
            data["students"] = UserProfile.objects.filter(role="student").count()
            data["couriers"] = UserProfile.objects.filter(role="courier").count()
        return Response(data)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = OrderReviewSerializer

    def get_queryset(self):
        return OrderReview.objects.filter(reviewer=self.request.user)

    def perform_create(self, serializer):
        try:
            order = DeliveryOrder.objects.get(pk=self.request.data.get("order"))
        except DeliveryOrder.DoesNotExist:
            raise serializers.ValidationError({"order": "订单不存在"})
        if order.requester != self.request.user or order.status != "completed":
            raise serializers.ValidationError({"order": "只有已完成的本人订单可以评价"})
        if OrderReview.objects.filter(order=order).exists():
            raise serializers.ValidationError({"order": "该订单已经评价过"})
        serializer.save(reviewer=self.request.user)
