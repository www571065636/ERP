from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        code = response.status_code
        if code == 401:
            msg = "未认证或 Token 已过期"
        elif code == 403:
            msg = "无操作权限"
        elif code == 404:
            msg = "资源不存在"
        else:
            data = response.data
            if isinstance(data, dict):
                msg = "; ".join(
                    f"{k}: {v[0] if isinstance(v, list) else v}"
                    for k, v in data.items()
                )
            else:
                msg = str(data)
        response.data = {"code": code, "msg": msg, "data": None}
    return response
