#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 4/30/2024 5:26 PM
# @Author : Ruinan Zhang
# @File : urls.py
# @Description:

from django.urls import include, path
from file import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('disk',views.FileViews,basename='FileViews')
urlpatterns = [
    path('api/file/', include(router.urls)),
]
