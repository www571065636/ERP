from django.core.validators import RegexValidator, EmailValidator

# 手机号：1 开头 11 位数字
phone_validator = RegexValidator(
    regex=r'^1[3-9]\d{9}$',
    message='请输入有效的手机号（11位数字，1开头）'
)

# 座机/固话：区号-号码，如 010-12345678
landline_validator = RegexValidator(
    regex=r'^\d{3,4}-\d{7,8}$',
    message='请输入有效的座机号（格式：区号-号码，如 010-12345678）'
)

# 手机或座机均可
phone_or_landline_validator = RegexValidator(
    regex=r'^(1[3-9]\d{9}|\d{3,4}-\d{7,8})$',
    message='请输入有效的手机号或座机号'
)

# 邮箱
email_validator = EmailValidator(message='请输入有效的邮箱地址')
