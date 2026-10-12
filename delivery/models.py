import uuid
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = (("student", "学生"), ("courier", "配送员"), ("admin", "管理员"))
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    phone = models.CharField(max_length=20, blank=True)
    campus = models.CharField(max_length=100, default="主校区")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}({self.get_role_display()})"


class DeliveryOrder(models.Model):
    TYPE_CHOICES = (("package", "快递代取"), ("food", "外卖配送"), ("item", "物品帮送"), ("other", "其他"))
    STATUS_CHOICES = (
        ("pending", "待接单"), ("accepted", "已接单"), ("picking", "取件中"),
        ("delivering", "配送中"), ("completed", "已完成"), ("cancelled", "已取消"),
    )
    order_no = models.CharField(max_length=32, unique=True, editable=False)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="delivery_orders")
    courier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="courier_orders")
    order_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="package")
    pickup_address = models.CharField(max_length=200)
    delivery_address = models.CharField(max_length=200)
    item_description = models.CharField(max_length=200)
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=3)
    note = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if not self.order_no:
            self.order_no = "CD" + uuid.uuid4().hex[:14].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_no


class OrderReview(models.Model):
    order = models.OneToOneField(DeliveryOrder, on_delete=models.CASCADE, related_name="review")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    content = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

