# -*- coding: utf-8 -*-#

#-------------------------------------------------------------------------------
# Name:         urls
# Description:
# Author:       XiaoM
# Date:         2020/6/23
#-------------------------------------------------------------------------------

# 进行users子应用的视图路由
from django.urls import path
from users.views import RegistView, ImageCodeView

urlpatterns = [
    #path的第一个参数，路由
    #path的第二个参数，视图函数名
    path('register/', RegistView.as_view(), name='register'),
    #图片验证码路由
    path('imagecode/', ImageCodeView.as_view(), name='imagecode'),

]