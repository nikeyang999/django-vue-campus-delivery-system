from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from delivery.models import DeliveryOrder, UserProfile


class Command(BaseCommand):
    help = "创建校园配送系统演示账号和订单"

    def ensure_user(self, username, role):
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password("123456")
            user.save()
        UserProfile.objects.update_or_create(user=user, defaults={"role": role, "campus": "主校区"})
        return user

    def handle(self, *args, **options):
        student = self.ensure_user("student", "student")
        courier = self.ensure_user("courier", "courier")
        admin = self.ensure_user("admin", "admin")
        if not DeliveryOrder.objects.exists():
            DeliveryOrder.objects.create(requester=student, courier=courier, order_type="package",
                pickup_address="东门菜鸟驿站", delivery_address="南区3栋205",
                item_description="教材和日用品", fee=4, status="accepted")
            DeliveryOrder.objects.create(requester=student, order_type="food",
                pickup_address="商业街奶茶店", delivery_address="北区2栋101",
                item_description="奶茶一杯", fee=3, note="请放在宿管处")
        self.stdout.write(self.style.SUCCESS("演示数据创建完成：student/courier/admin，密码均为 123456"))

