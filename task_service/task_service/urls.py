"""task_service URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from task_service import views
from task_service import access_control

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('auth_callback/', access_control.auth_callback),
    path('login/', access_control.redirect_to_login),
    path('user/', access_control.get_user_info),
    
    path('task/', views.get_task),
    # TODO: rest naming
    path('add_task/', views.add_task),
    # path('update_task/', views.update_task,
    # path('shuffle_tasks/', views.shuffle_tasks),
]
