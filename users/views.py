
from django.shortcuts import render

# Create your views here.

#注册视图
from django.views import View
from django.http.response import HttpResponseBadRequest, JsonResponse
import re
from users.models import User
from django.db import DatabaseError
from django.shortcuts import redirect
from django.urls import reverse
class RegistView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        """
        1.接受数据
        2.验证数据
            2.1 参数是否齐全
            2.2 手机号格式是否正确
            2.3 密码是否符合格式
            2.4 密码是否一致
            2.5 短信验证码是否和redis中一致
        3.保存注册信息
        4.返回响应跳转导致指定页面
        :param request:
        :return:
        """
        # 1.接受数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')
        # 2.验证数据
        #     2.1 参数是否齐全
        if not all([mobile, password, password2, smscode]):
            return HttpResponseBadRequest('缺少必要参数')
        #     2.2 手机号格式是否正确
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号码不符合规则')
        #     2.3 密码是否符合格式
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('请输入8-20位密码，密码由数字和字母组成')
        #     2.4 密码是否一致
        if password != password2:
            return HttpResponseBadRequest('密码不一致')
        #     2.5 短信验证码是否和redis中一致
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s' % mobile)
        if redis_sms_code is None:
            return HttpResponseBadRequest('短信验证码已过期')
        if smscode != redis_sms_code.decode():
            return HttpResponseBadRequest('短信验证不一致')
        # 3.保存注册信息
        # create_user可以使用系统的方法来对密码加密
        try:
            user = User.objects.create_user(username=mobile,
                                            mobile=mobile,
                                            password=password)
        except DatabaseError as e:
            logger.error(e)
            return HttpResponseBadRequest('注册失败')

        from django.contrib.auth import login
        login(request, user)
        # 4.返回响应跳转导致指定页面
        #暂时返回一个注册成功的信息，后期再实现跳转到制定页面
        # return HttpResponse('注册成功，重定向到页面')
        #redirect是重定向
        #reverse是可以通过namespace:name来获取视图对应的路由
        response = redirect(reverse('home:index'))
        #return HttpResponse，表示注册成功，重定向到首页

        # 设置cookie信息，以方便首页中用户信息展示和判断
        response.set_cookie('is_login', True)
        response.set_cookie('username', user.username, max_age=7*24*3600)
        return response
from django.http.response import HttpResponseBadRequest, JsonResponse
from django.http.response import HttpResponse
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection

#图片验证码
class ImageCodeView(View):

    def get(self, request):
        """
        1.接受前端传递来的uuid
        2.判断uuid是否获取成功
        3.通过电泳查平台查来生成图片验证码(图片二进制，图片内容文)
        4.图片内容保存到Redis中
          uuid作为key,图片内容作为value，同时还需要设置时效
        5.图片二进制返归给前端
        """
        # 1.接受前端传递来的uuid
        uuid = request.GET.get('uuid')
        # 2.判断uuid是否获取成功
        if uuid is None:
            return HttpResponseBadRequest('传递uuid错误')
        # 3.通过电泳查平台查来生成图片验证码(图片二进制，图片内容文)
        text,image = captcha.generate_captcha()
        # 4.图片内容保存到Redis中
        # uuid作为key, 图片内容作为value，同时还需要设置时效
        redis_conn = get_redis_connection('default')
        #key设置为uuid
        #seconds 过期秒数300秒过期
        #value设置为text
        redis_conn.setex('img:%s' %uuid, 300, text)
        # 5.图片二进制返归给前端
        return HttpResponse(image, content_type='image/jpeg')

# 短信验证码
from django.http.response import JsonResponse
from utils.response_code import RETCODE
import logging
logger = logging.getLogger('djangologger')
from random import randint
from libs.yuntongxun.sms import CCP

class SmsCodeView(View):

    def get(self, request):
        """
        1.接收参数
        2.参数的验证
        2.1 验证参数是否齐全
        2.2 图片验证码的验证
            连接redis,获取redis中的图片验证码
            判断图片验证码是否存在
            如果图片验证码未过期，我们获取到之后就可以将其删除
            对比图片验证码
        3.生成短信验证码
        4.保存短信验证码到redis中
        5.发送短信
        6.返回响应
        :param request:
        :return:
        """
        # 1.接收参数(查询字符串的形式传递)
        mobile = request.GET.get('mobile')
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        # 2.参数的验证
        # 2.1 参数是否齐全
        if not all([mobile, image_code, uuid]):
            return JsonResponse({'code':RETCODE.NECESSARYPARAMERR,'errmsg':'缺少必要的参数'})
        # 2.2图片验证码的验证
        # 连接redis, 获取redis中的图片验证码
        redis_conn = get_redis_connection('default')
        redis_image_code = redis_conn.get('img:%s'% uuid)
        # 判断图片验证码是否存在
        if redis_image_code is None:
            return JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图片验证码已过期'})
        # 如果图片验证码未过期，我们获取到之后就可以将其删除
        try:
            redis_conn.delete('img:%s'% uuid)
        except Exception as e:
            logger.error(e)
            # 对比图片验证码,注意大小写，redis的数据是byte类型
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图片验证码错误'})
        # 3.生成短信验证码
        sms_code = '%06d' %randint(0, 999999)
        #为了方便可以将短信验证码记录到日志
        logger.info(sms_code)
        # 4.保存短信验证码到redis中
        redis_conn.setex('sms:%s'% mobile, 300, sms_code)
        # 5.发送短信
        CCP().send_template_sms(mobile, [sms_code, 5], 1)
        # 6.返回响应
        return JsonResponse({'code':RETCODE.OK, 'errmsg':'短信发送成功'})

# 登陆实现
class LoginView(View):

    def get(self, request):

        return render(request, 'login.html')
    def post(self, request):
        """
        1.参数接收
        2.参数验证
            2.1 验证手机号
            2.2 验证密码
        3.用户认证登陆
        4.状态保持
        5.根据用户选择的时候记住登录状态来进行判断
        6.为了首页显示，我们需要设置cookie信息
        7.返回响应
        :param request:
        :return:
        """
        # 1.参数接收
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        # 2.参数验证
        #     2.1 验证手机号
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号码不符合规则')
        #     2.2 验证密码
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('密码不符合规则')
        # 3.用户认证登陆
            #采用自带的认证方法进行认证
            #如果用户名和密码正确，返回user
            #如果用户名和密码不正确，None
        from django.contrib.auth import authenticate
        #磨人的认证方法是针对username字段进行用户名判断
        #当前的判断信息是手机号码，所以我们需要修改一下认证字段
        #需要到user模型中进行修改，等测试出现问题时候在进行修改
        user = authenticate(mobile=mobile, password=password)
        if user is None:
            return HttpResponseBadRequest('用户名密码错误')

        # 4.状态保持
        from django.contrib.auth import login
        login(request, user)
        # 5.根据用户选择的时候记住登录状态来进行判断
        # 为了首页显示，我们需要设置cookie信息

        #根据next参数进行页面跳转
        next_page = request.GET.get('next')
        if next_page:
            response = redirect(next_page)
        else:
            response = redirect(reverse('home:index'))
        if remember != 'on':    #没有记住用户信息
            request.session.set_expiry(0)
            response.set_cookie('is_login', True)
            response.set_cookie('username', user.username, max_age=14*24*3600)
        else:                   #记住用户信息
            #默认是记住2周
            request.session.set_expiry(None)
            response.set_cookie('is_login', True, max_age=14*24*3600)
            response.set_cookie('username', user.username, max_age=14*24*3600)

        # 6.返回响应
        return response
#退出登录
from django.contrib.auth import logout
class LogOutView(View):

    def get(self, request):
        # 1. session 数据清除
        logout(request)
        # 2.删除部分cookie信息
        response = redirect(reverse('home:index'))
        response.delete_cookie('is_login')
        # 3. 跳转到主页
        return response

#忘记密码
class ForgetPasswordView(View):
    def get(self, request):

        return render(request, 'forget_password.html')

    def post(self, request):
        """
        1.接收数据
        2.验证数据
        3.用户信息查询
        4.如果手机号查询成功，修改密码
        5.未查出，注册新用户
        6.页面重定向登录页面
        7.返回响应
        :param request:
        :return:
        """
        # 1.接收数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')
        # 2.验证数据
        if not all([mobile, password, password2, smscode]):
            return HttpResponseBadRequest('参数不全')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号不符合规范')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('请输入8-20位密码，密码是字母和数字')
        if password != password2:
            return HttpResponseBadRequest('两次密码不一致')
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s' % mobile)
        if redis_sms_code is None:
            return HttpResponseBadRequest('短信验证码已过期')
        if smscode != redis_sms_code.decode():
            return HttpResponseBadRequest('短信验证码错误')
        # 3.用户信息查询
        try:
            user = User.objects.get(mobile = mobile)
        except User.DoesNotExist:
            # 5.未查出，注册新用户
            try:
                User.objects.create_user(username=mobile,
                                     mobile=mobile,
                                     password=password)
            except Exception:
                return HttpResponseBadRequest('创建失败，请稍后重试')
        else:
            # 4.如果手机号查询成功，修改密码
            user.set_password(password)
            user.save()
        # 6.页面重定向登录页面
        response = redirect(reverse('users:login'))
        # 7.返回响应
        return response

#用户中心实现
# class UserCenterView(View):
#     def get(self, request):
#
#         return render(request, 'center.html')

from django.contrib.auth.mixins import LoginRequiredMixin
# 如果用户未登录，进行默认跳转
# 默认跳转路由是： accounts/login?next=xxx
class UserCenterView(LoginRequiredMixin, View):

    def get(self, request):
        # 获取登录信息
        user = request.user
        # 组织获取用户信息
        context = {
            'username': user.username,
            'mobile': user.mobile,
            'avatar': user.avatar.url if user.avatar else None,
            'user_desc':user.user_desc
        }
        return render(request, 'center.html', context=context)

    def post(self, request):
        """
        1.接收参数
        2.将参数保存
        3.跟新cookie信息
        4.刷新当前页面（重定向）
        5.返回响应
        :param request:
        :return:
        """
        user = request.user
        # 1.接收参数
        username = request.POST.get('username', user.username)
        user_desc = request.POST.get('desc', user.user_desc)
        avatar = request.FILES.get('avatar')
        # 2.将参数保存
        try:
            user.username = username
            user.user_desc = user_desc
            if avatar:
                user.avatar = avatar
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('修改失败请稍后再试')
        # 3.更新cookie信息
        # 4.刷新当前页面（重定向）
        response = redirect(reverse('users:center'))
        response.set_cookie('username', user.username, max_age=1800)
        # 5.返回响应
        return response
#写博客实现
from home.models import ArticleCategory, Article
class WriteBlogView(LoginRequiredMixin, View):

    def get(self, request):
        # 查询所有分类
        categories = ArticleCategory.objects.all()

        context = {
            'categories':categories
        }
        return render(request, 'write_blog.html', context=context)

    def post(self, request):
        """
        1.接收数据
        2.验证数据
        3.数据入库
        4.跳转到指定页面（暂时首页）
        :param request:
        :return:
        """
        # 1.接收数据
        avatar = request.FILES.get('avatar')
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        tags = request.POST.get('tags')
        summary = request.POST.get('sumary')
        content = request.POST.get('content')
        user = request.user
        # 2.验证数据
        if not all([avatar, title, category_id, tags, summary, content]):
            return HttpResponseBadRequest('参数不全')
        try:
            category = ArticleCategory.objects.get(id = category_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseBadRequest('没有此分类')
        # 3.数据入库
        try:
            article = Article.objects.create(
                author=user,
                avatar=avatar,
                title=title,
                tags=tags,
                category=category,
                summary=summary,
                content=content,
            )
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('发布失败，请稍后再试')
        # 4.跳转到指定页面（暂时首页
        return redirect(reverse('home:index'))