from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.utils import timezone

from .models import User, Role, Permission
from .serializers import (
    UserSerializer, UserCreateSerializer,
    RoleSerializer, PermissionSerializer, PermissionTreeSerializer, get_user_permission_codes,
)
from common.permissions import HasPermCode
from common.response import ok, fail
from hr.models import Employee
from inventory.models import Stock, Warehouse
from product.models import Product
from purchase.models import PurchaseOrder, Supplier
from sales.models import Customer, SalesOrder


class LoginRateThrottle(ScopedRateThrottle):
    scope = "login"


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in ["me", "change_password", "logout"]:
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def get_throttles(self):
        if self.action == "login":
            return [LoginRateThrottle()]
        return [throttle() for throttle in self.throttle_classes]

    @action(detail=False, methods=["post"])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if not user:
            return fail("账号或密码错误", 401)
        if not user.status:
            return fail("账号已被禁用", 403)
        now = timezone.now()
        user.last_login_at = now
        user.last_login_ip = request.META.get("REMOTE_ADDR", "")
        user.save(update_fields=["last_login_at", "last_login_ip"])
        refresh = RefreshToken.for_user(user)
        perms = get_user_permission_codes(user)
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
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        user = request.user
        old_pw = request.data.get("old_password")
        new_pw = request.data.get("new_password")
        if not user.check_password(old_pw):
            return fail("原密码错误")
        try:
            validate_password(new_pw, user=user)
        except ValidationError as e:
            return fail("；".join(e.messages))
        user.set_password(new_pw)
        user.save(update_fields=["password"])
        return ok(msg="密码修改成功")


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_deleted=False).order_by("-created_at")
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["status", "dept_id"]
    search_fields = ["username", "real_name", "mobile"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "system:user:list",
        "retrieve": "system:user:list",
        "create": "system:user:create",
        "update": "system:user:update",
        "partial_update": "system:user:update",
        "destroy": "system:user:delete",
        "roles": "system:user:assign-role",
        "status": "system:user:status",
    }

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
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "system:role:list",
        "retrieve": "system:role:list",
        "create": "system:role:create",
        "update": "system:role:update",
        "partial_update": "system:role:update",
        "destroy": "system:role:delete",
        "permissions": "system:role:assign-permission",
    }

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
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "system:permission:list",
        "retrieve": "system:permission:list",
        "tree": "system:permission:list",
        "create": "system:permission:create",
        "update": "system:permission:update",
        "partial_update": "system:permission:update",
        "destroy": "system:permission:delete",
    }

    @action(detail=False, methods=["get"])
    def tree(self, request):
        all_perms = list(self.get_queryset())
        roots = [p for p in all_perms if p.parent_id == 0]
        data = PermissionTreeSerializer(roots, many=True, context={"all_perms": all_perms}).data
        return ok(data)


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        from django.db.models import F, OuterRef, Subquery

        today = timezone.localdate()
        month_start = today.replace(day=1)

        # 库存预警：用子查询关联 Product.min_stock，单次 DB 查询完成
        min_stock_subquery = Product.objects.filter(
            id=OuterRef("product_id"),
            is_deleted=False,
            min_stock__gt=0,
        ).values("min_stock")[:1]
        stock_alerts = (
            Stock.objects.filter(is_deleted=False)
            .annotate(_min_stock=Subquery(min_stock_subquery))
            .filter(_min_stock__isnull=False, qty_available__lt=F("_min_stock"))
            .count()
        )

        pending_count = (
            PurchaseOrder.objects.filter(is_deleted=False, status=1).count()
            + SalesOrder.objects.filter(is_deleted=False, status=1).count()
        )

        counts = {
            "purchase_orders": PurchaseOrder.objects.filter(is_deleted=False).count(),
            "sales_orders": SalesOrder.objects.filter(is_deleted=False).count(),
            "employees": Employee.objects.filter(is_deleted=False).count(),
            "products": Product.objects.filter(is_deleted=False).count(),
            "suppliers": Supplier.objects.filter(is_deleted=False).count(),
            "customers": Customer.objects.filter(is_deleted=False).count(),
            "warehouses": Warehouse.objects.filter(is_deleted=False).count(),
            "month_orders": (
                PurchaseOrder.objects.filter(is_deleted=False, order_date__gte=month_start).count()
                + SalesOrder.objects.filter(is_deleted=False, order_date__gte=month_start).count()
            ),
        }

        data = {
            "stat_cards": [
                {"title": "采购订单", "value": counts["purchase_orders"]},
                {"title": "销售订单", "value": counts["sales_orders"]},
                {"title": "库存预警", "value": stock_alerts},
                {"title": "员工总数", "value": counts["employees"]},
            ],
            "overview": [
                {"label": "产品总数", "value": counts["products"]},
                {"label": "供应商数", "value": counts["suppliers"]},
                {"label": "客户数", "value": counts["customers"]},
                {"label": "仓库数", "value": counts["warehouses"]},
                {"label": "待审批", "value": pending_count},
                {"label": "本月订单", "value": counts["month_orders"]},
            ],
        }
        return ok(data)
