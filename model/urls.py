from django.urls import include, path
from model import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("network", views.NetworkView, basename="NetworkView")
router.register("weight", views.WeightView, basename="WeightView")
router.register("dict", views.NetworkWeightView, basename="NetworkWeightView")
router.register("cloudWeight", views.CloudWeightView, basename="CloudWeightView")
urlpatterns = [
    path("api/model/", include(router.urls)),
]
