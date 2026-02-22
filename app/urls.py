from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    path("", home, name="home"),
    path("test/", test_page, name="test"),
    path("test-values/", values_test, name="values_test"),
    path("upload-audio/", upload_audio, name="upload_audio"),
    path("record-audio/", record_and_detect, name="record_audio"),
    path("predict-values/", values_predict, name="values_predict"),
    path("history/", history, name="history"),
    path("detection/<int:detection_id>/", detection_detail, name="detection_detail"),
    path("profile/", profile, name="profile"),
    path("download-report/<int:detection_id>/", download_report, name="download_report"),
    path("initialize-hospitals/", initialize_hospitals, name="initialize_hospitals"),
]