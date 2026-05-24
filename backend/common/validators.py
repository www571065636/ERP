from django.core.validators import RegexValidator, EmailValidator

# 手机号：1 开头 11 位数字
phone_validator = RegexValidator(
    regex=r'^1[3-9]\d{9}$',
    message='请输入有效的手机号（11位数字，1开头）'
)

# 邮箱
email_validator = EmailValidator(message='请输入有效的邮箱地址')
