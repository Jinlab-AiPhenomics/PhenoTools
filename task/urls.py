#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 4/30/2024 5:26 PM
# @Author : Ruinan Zhang
# @File : urls.py
# @Description:

from django.urls import include, path
from task.views import prediction_task, training_task, utils
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(
    "configuration", utils.TaskConfigurationView, basename="TaskConfigurationView"
)
router.register("summary", utils.TaskSummaryView, basename="TaskSummaryView")
router.register("training", training_task.TrainingTaskView, basename="TrainingTaskView")
router.register(
    "prediction", prediction_task.PredictionTaskView, basename="PredictionTaskView"
)
router.register("log", utils.TaskLogView, basename="TaskLogView")
router.register("imgPreview", utils.ImagePreviewView, basename="ImagePreviewView")
router.register("stop", utils.StopTaskView, basename="StopTaskView")
urlpatterns = [
    path("api/task/", include(router.urls)),
]
