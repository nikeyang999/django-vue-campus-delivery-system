from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import DeliveryOrderViewSet, LoginView, MeView, RegisterView, ReviewViewSet

router = DefaultRouter()
router.register("orders", DeliveryOrderViewSet, basename="orders")
router.register("reviews", ReviewViewSet, basename="reviews")

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("", include(router.urls)),
]

