from rest_framework import serializers
from .models import User, Role, Permission


def get_user_permission_codes(user):
    return list(
        Permission.objects.filter(
            roles__users=user,
            roles__status=True,
            roles__is_deleted=False,
            perm_code__gt="",
            is_deleted=False,
        ).values_list("perm_code", flat=True).distinct()
    )


class UserSerializer(serializers.ModelSerializer):
    role_ids = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "real_name", "avatar", "email", "mobile",
                  "dept_id", "status", "last_login_ip", "last_login_at", "created_at", "role_ids", "permissions"]
        read_only_fields = ["id", "created_at", "last_login_ip", "last_login_at"]

    def get_role_ids(self, obj):
        return list(obj.roles.values_list("id", flat=True))

    def get_permissions(self, obj):
        return get_user_permission_codes(obj)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = User
        fields = ["username", "password", "real_name", "email", "mobile", "dept_id", "role_ids"]

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError("；".join(e.messages))
        return value

    def create(self, validated_data):
        role_ids = validated_data.pop("role_ids", [])
        user = User.objects.create_user(**validated_data)
        if role_ids:
            user.roles.set(role_ids)
        return user


class RoleSerializer(serializers.ModelSerializer):
    permission_ids = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "role_name", "role_code", "data_scope", "sort_order",
                  "remark", "status", "created_at", "permission_ids"]
        read_only_fields = ["id", "created_at"]

    def get_permission_ids(self, obj):
        return list(obj.permissions.values_list("id", flat=True))


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "parent_id", "perm_name", "perm_code", "perm_type",
                  "path", "component", "icon", "sort_order", "is_visible"]


class PermissionTreeSerializer(PermissionSerializer):
    children = serializers.SerializerMethodField()

    class Meta(PermissionSerializer.Meta):
        fields = PermissionSerializer.Meta.fields + ["children"]

    def get_children(self, obj):
        children = [p for p in self.context.get("all_perms", []) if p.parent_id == obj.id]
        return PermissionTreeSerializer(children, many=True, context=self.context).data
