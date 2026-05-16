from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .models import User, Role, Permission
from .serializers import (
    UserSerializer, UserCreateSerializer,
    RoleSerializer, PermissionSerializer, PermissionTreeSerializer,
)
from common.response import ok, fail


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if not user:
            return fail("账号或密码错误", 401)
        if not user.status:
            return fail("账号已被禁用", 403)
        refresh = RefreshToken.for_user(user)
        perms = list(
            Permission.objects.filter(
                roles__users=user, perm_code__gt=""
            ).values_list("perm_code", flat=True).distinct()
        )
        return ok({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "real_name": user.real_name,
                "avatar": user.avatar,
                "permissions": perms,
            }
        })

    @action(detail=False, methods=["post"])
    def logout(self, request):
        try:
            token = RefreshToken(request.data.get("refresh"))
            token.blacklist()
        except Exception:
            pass
        return ok(msg="已登出")

    @action(detail=False, methods=["get"])
    def me(self, request):
        return ok(UserSerializer(request.user).data)

    @action(detail=False, methods=["put"], url_path="me/password")
    def change_password(self, request):
        user = request.user
        old_pw = request.data.get("old_password")
        new_pw = request.data.get("new_password")
        if not user.check_password(old_pw):
            return fail("原密码错误")
        if len(new_pw) < 6:
            return fail("新密码至少6位")
        user.set_password(new_pw)
        user.save(update_fields=["password"])
        return ok(msg="密码修改成功")


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_deleted=False).order_by("-created_at")
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["status", "dept_id"]
    search_fields = ["username", "real_name", "mobile"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        return super().get_queryset().exclude(is_superuser=True)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.id)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")

    @action(detail=True, methods=["put"])
    def roles(self, request, pk=None):
        user = self.get_object()
        role_ids = request.data.get("role_ids", [])
        user.roles.set(role_ids)
        return ok(msg="角色分配成功")

    @action(detail=True, methods=["put"])
    def status(self, request, pk=None):
        user = self.get_object()
        user.status = bool(request.data.get("status", True))
        user.save(update_fields=["status"])
        return ok(msg="状态更新成功")


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.filter(is_deleted=False).order_by("sort_order")
    serializer_class = RoleSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")

    @action(detail=True, methods=["put"])
    def permissions(self, request, pk=None):
        role = self.get_object()
        perm_ids = request.data.get("permission_ids", [])
        role.permissions.set(perm_ids)
        return ok(msg="权限分配成功")


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.filter(is_deleted=False).order_by("sort_order")
    serializer_class = PermissionSerializer

    @action(detail=False, methods=["get"])
    def tree(self, request):
        all_perms = list(self.get_queryset())
        roots = [p for p in all_perms if p.parent_id == 0]
        data = PermissionTreeSerializer(roots, many=True, context={"all_perms": all_perms}).data
        return ok(data)
