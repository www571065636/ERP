from rest_framework.response import Response


def ok(data=None, msg="success"):
    return Response({"code": 200, "msg": msg, "data": data})


def fail(msg, code=400, data=None):
    return Response({"code": code, "msg": msg, "data": data}, status=code)
