from django.urls import include, path
from dataset import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("dataset", views.DatasetView, basename="DatasetView")
urlpatterns = [
    path("api/", include(router.urls)),
]
