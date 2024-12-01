from django.urls import include, path
from model import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('network',views.NetworkView,basename='NetworkView')
router.register('weight',views.WeightView,basename='WeightView')
router.register('dict',views.NetworkWeightView,basename='NetworkWeightView')
urlpatterns = [
    path('api/model/', include(router.urls)),
]
