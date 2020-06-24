from django.shortcuts import render

# Create your views here.

#注册视图
from django.views import View

class RegistView(View):
    def get(self, request):
        return render(request, 'register.html')

#
from django.http.response import HttpResponseBadRequest
from django.http.response import HttpResponse
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection

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
            return HttpResponseBadRequest('传递uuid错误！')
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