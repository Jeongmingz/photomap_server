from django.urls import path

from apis.apis import qr_photo_check_api

urlpatterns = [
    path('qr', qr_photo_check_api, name='qr-photo'),
]
