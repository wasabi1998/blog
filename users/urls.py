# -*- coding: utf-8 -*-#

#-------------------------------------------------------------------------------
# Name:         urls
# Description:
# Author:       XiaoM
# Date:         2020/6/23
#-------------------------------------------------------------------------------

# 进行users子应用的视图路由
from django.urls import path
from users.views import RegistView
from users.views import ImageCodeView
from users.views import SmsCodeView
from users.views import LoginView
from users.views import LogOutView
from users.views import ForgetPasswordView
from users.views import UserCenterView
from users.views import WriteBlogView

urlpatterns = [
    #path的第一个参数，路由
    #path的第二个参数，视图函数名
    path('register/', RegistView.as_view(), name='register'),
    #图片验证码路由
    path('imagecode/', ImageCodeView.as_view(), name='imagecode'),
    #短信发送路由
    path('smscode/', SmsCodeView.as_view(), name='smscode'),
    #登陆路由
    path('login/', LoginView.as_view(), name='login'),
    #登陆退出路由
    path('logout/', LogOutView.as_view(), name='logout'),
    #忘记密码路由
    path('forgetpassword/', ForgetPasswordView.as_view(), name='forgetpassword'),
    #用户中心路由
    path('center/', UserCenterView.as_view(), name='center'),
# 博客发布
    path('writeblog/', WriteBlogView.as_view(), name='writeblog'),
]