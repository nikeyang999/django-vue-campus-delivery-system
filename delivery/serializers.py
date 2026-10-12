from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import DeliveryOrder, OrderReview, UserProfile


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)
    phone = serializers.CharField(source="profile.phone", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "role", "phone")


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=30)
    password = serializers.CharField(min_length=6, write_only=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=("student", "courier"), default="student")

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在")
        return value

    def create(self, validated_data):
        role = validated_data.pop("role", "student")
        phone = validated_data.pop("phone", "")
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, role=role, phone=phone)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("用户名或密码错误")
        if not hasattr(user, "profile"):
            UserProfile.objects.create(user=user)
        attrs["user"] = user
        return attrs


class DeliveryOrderSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source="requester.username", read_only=True)
    courier_name = serializers.CharField(source="courier.username", read_only=True, default="")
    order_type_label = serializers.CharField(source="get_order_type_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = DeliveryOrder
        fields = ("id", "order_no", "requester", "requester_name", "courier", "courier_name",
                  "order_type", "order_type_label", "pickup_address", "delivery_address",
                  "item_description", "fee", "note", "status", "status_label", "created_at",
                  "updated_at", "accepted_at", "completed_at")
        read_only_fields = ("order_no", "requester", "courier", "status", "accepted_at", "completed_at")


class OrderReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderReview
        fields = ("id", "order", "reviewer", "rating", "content", "created_at")
        read_only_fields = ("reviewer",)

