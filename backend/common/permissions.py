from rest_framework.permissions import BasePermission


class HasPermCode(BasePermission):
    message = "无操作权限"

    def has_permission(self, request, view):
        required = getattr(view, "permission_map", {}).get(getattr(view, "action", None))
        if not required:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if isinstance(required, str):
            required = [required]
        # 按请求缓存权限码，避免重复 DB 查询
        cache_key = f"_perm_cache_{user.id}"
        user_perms = getattr(request, cache_key, None)
        if user_perms is None:
            user_perms = set(
                user.roles.filter(status=True, is_deleted=False)
                .values_list("permissions__perm_code", flat=True)
            )
            user_perms.discard("")
            setattr(request, cache_key, user_perms)
        return all(code in user_perms for code in required)
