from django.shortcuts import render

# Create your views here.

#注册视图
from django.views import View

class RegistView(View):
    def get(self, request):
        return render(request, 'register.html')

#
from django.http.response import HttpResponseBadRequest, JsonResponse
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

from django.http.response import JsonResponse
from utils.response_code import RETCODE
import logging
logger = logging.getLogger('djangologger')
from random import randint
from libs.yuntongxun.sms import CCP

class SmsCodeView(View):

    def get(self, request):
        """
        1.接收各个参数
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
        # 1.接收各个参数(查询字符串的形式传递)
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