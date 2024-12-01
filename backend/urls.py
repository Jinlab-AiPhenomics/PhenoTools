from django.urls import path, include

urlpatterns = [
    path("", include("system.urls")),
    path("", include("task.urls")),
    path("", include("file.urls")),
    path("", include("model.urls")),
    path("", include("dataset.urls")),
]
