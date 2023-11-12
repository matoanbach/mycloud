from django.urls import path
from . import views

app_name = 'cloud'
urlpatterns = [
    path('', views.index, name='index'),
    path('upload', views.upload, name='upload'),
    path('file_list', views.file_list, name='file_list'),
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('download/<int:file_id>', views.download, name='donwload'),
    path('share/<int:file_id>', views.share, name='share')
]
