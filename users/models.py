from django.db import models

from django.contrib.auth.models import User, AbstractUser
# Create your models here.

class User(AbstractUser):
    #手机号
    mobile = models.CharField(max_length=11, unique=True, blank=False)
    #头像信息
    avatar = models.ImageField(upload_to='avatar/%Y%m%d', blank=True)
    #间接信息
    user_desc = models.CharField(max_length=500, blank=True)

    #修改认证的字段为手机号
    USERNAME_FIELD = 'mobile'

    # 创建超级管理员时需要必须设置的字段
    REQUIRED_FIELDS = ['username', 'email']

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.mobile