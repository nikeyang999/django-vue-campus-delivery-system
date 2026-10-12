from django.contrib import admin
from .models import DeliveryOrder, OrderReview, UserProfile

admin.site.register(UserProfile)
admin.site.register(DeliveryOrder)
admin.site.register(OrderReview)

