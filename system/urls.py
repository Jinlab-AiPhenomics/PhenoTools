#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 4/30/2024 5:26 PM
# @Author : Ruinan Zhang
# @File : urls.py
# @Description:

from django.urls import include, path
from system import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("info", views.SystemInfoViews, basename="SystemInfoViews")
router.register("log", views.SystemLogViews, basename="SystemLogViews")
router.register("setting", views.SystemSettingViews, basename="SystemSettingViews")
router.register("download", views.DownloadFileViews, basename="DownloadFileViews")
urlpatterns = [
    path("api/system/", include(router.urls)),
]
