from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from common.models import BaseModel
from common.validators import phone_validator, email_validator


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra):
        user = self.model(username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    username = models.CharField(max_length=64, unique=True, verbose_name="账号")
    real_name = models.CharField(max_length=64, verbose_name="姓名")
    avatar = models.CharField(max_length=255, blank=True, default="", verbose_name="头像")
    email = models.EmailField(blank=True, default="", verbose_name="邮箱", validators=[email_validator])
    mobile = models.CharField(max_length=20, blank=True, default="", db_index=True, verbose_name="手机号", validators=[phone_validator])
    dept_id = models.BigIntegerField(null=True, blank=True, db_index=True, verbose_name="部门ID")
    status = models.BooleanField(default=True, db_index=True, verbose_name="启用状态")
    is_staff = models.BooleanField(default=False)
    last_login_ip = models.CharField(max_length=64, blank=True, default="")
    last_login_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["real_name"]

    class Meta:
        db_table = "sys_user"
        verbose_name = "用户"

    def __str__(self):
        return self.username


class Role(BaseModel):
    role_name = models.CharField(max_length=64, verbose_name="角色名称")
    role_code = models.CharField(max_length=64, unique=True, verbose_name="角色编码")
    data_scope = models.SmallIntegerField(default=1, verbose_name="数据权限")
    sort_order = models.IntegerField(default=0)
    remark = models.CharField(max_length=500, blank=True, default="")
    status = models.BooleanField(default=True, db_index=True)
    users = models.ManyToManyField(User, through="UserRole", related_name="roles", blank=True)

    class Meta:
        db_table = "sys_role"
        verbose_name = "角色"

    def __str__(self):
        return self.role_name


class Permission(BaseModel):
    parent_id = models.BigIntegerField(default=0, db_index=True, verbose_name="父节点ID")
    perm_name = models.CharField(max_length=64, verbose_name="权限名称")
    perm_code = models.CharField(max_length=128, blank=True, default="", db_index=True, verbose_name="权限标识")
    perm_type = models.SmallIntegerField(verbose_name="类型 1目录 2菜单 3按钮")
    path = models.CharField(max_length=255, blank=True, default="", verbose_name="路由路径")
    component = models.CharField(max_length=255, blank=True, default="", verbose_name="组件路径")
    icon = models.CharField(max_length=64, blank=True, default="")
    sort_order = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    roles = models.ManyToManyField(Role, through="RolePermission", related_name="permissions", blank=True)

    class Meta:
        db_table = "sys_permission"
        verbose_name = "权限"

    def __str__(self):
        return self.perm_name


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        db_table = "sys_user_role"
        unique_together = ("user", "role")


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = "sys_role_permission"
        unique_together = ("role", "permission")
