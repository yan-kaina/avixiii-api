from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class UserRole(models.TextChoices):
    ADMIN = 'admin', _('Administrator')
    STAFF = 'staff', _('Staff')
    CUSTOMER = 'customer', _('Customer')

class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser
    """
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        verbose_name=_('role')
    )
    is_email_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Required fields when creating a user
    REQUIRED_FIELDS = ['email', 'role']

    class Meta:
        db_table = 'auth_users'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_staff_member(self):
        return self.role == UserRole.STAFF

    @property
    def is_customer(self):
        return self.role == UserRole.CUSTOMER

class LoginAttempt(models.Model):
    """
    Model to track login attempts
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_attempts')
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    failure_reason = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'auth_login_attempts'
        ordering = ['-timestamp']

    def __str__(self):
        status = 'Success' if self.success else 'Failed'
        return f"{status} login attempt by {self.user.email} from {self.ip_address}"

class PasswordReset(models.Model):
    """
    Model to handle password reset requests
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=64, unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_ip = models.GenericIPAddressField()

    class Meta:
        db_table = 'auth_password_resets'
        ordering = ['-created_at']

    def __str__(self):
        status = 'Used' if self.is_used else 'Active'
        return f"{status} password reset token for {self.user.email}"

class SecurityLog(models.Model):
    """
    Model to log security-related events
    """
    class EventType(models.TextChoices):
        PASSWORD_CHANGE = 'password_change', _('Password Change')
        EMAIL_CHANGE = 'email_change', _('Email Change')
        ROLE_CHANGE = 'role_change', _('Role Change')
        ACCOUNT_LOCK = 'account_lock', _('Account Lock')
        ACCOUNT_UNLOCK = 'account_unlock', _('Account Unlock')
        LOGIN_SUCCESS = 'login_success', _('Login Success')
        LOGIN_FAILURE = 'login_failure', _('Login Failure')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs')
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auth_security_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_event_type_display()} for {self.user.email}"
