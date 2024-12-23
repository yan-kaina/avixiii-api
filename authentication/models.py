from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from django.core.cache import cache

class UserRole(models.TextChoices):
    ADMIN = 'admin', _('Administrator')
    STAFF = 'staff', _('Staff')
    CUSTOMER = 'customer', _('Customer')

class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser
    """
    email = models.EmailField(
        _('email address'),
        unique=True,
        validators=[EmailValidator()],
        error_messages={
            'unique': _('A user with that email already exists.'),
        }
    )
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        verbose_name=_('role'),
        db_index=True
    )
    is_email_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Required fields when creating a user
    REQUIRED_FIELDS = ['email', 'role']

    class Meta:
        db_table = 'auth_users'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['username']),
            models.Index(fields=['is_email_verified']),
        ]

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

    def increment_failed_login(self):
        """Increment failed login attempts and handle account locking"""
        from django.utils import timezone
        from datetime import timedelta

        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()

        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timedelta(minutes=30)
            SecurityLog.objects.create(
                user=self,
                event_type=SecurityLog.EventType.ACCOUNT_LOCK,
                details={'reason': 'Too many failed login attempts'}
            )

        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])

    def reset_failed_login(self):
        """Reset failed login attempts counter"""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.account_locked_until = None
            self.save(update_fields=['failed_login_attempts', 'account_locked_until'])

    def is_account_locked(self):
        """Check if account is currently locked"""
        from django.utils import timezone
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False

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
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]

    def __str__(self):
        status = 'Success' if self.success else 'Failed'
        return f"{status} login attempt by {self.user.email} from {self.ip_address}"

    @classmethod
    def check_ip_rate_limit(cls, ip_address):
        """Check if IP has exceeded rate limit"""
        cache_key = f'login_attempts_ip_{ip_address}'
        attempts = cache.get(cache_key, 0)
        if attempts >= 10:  # Limit to 10 attempts per minute
            return False
        cache.set(cache_key, attempts + 1, 60)  # 60 seconds timeout
        return True

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
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        status = 'Used' if self.is_used else 'Active'
        return f"{status} password reset token for {self.user.email}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expires_at < timezone.now()

    def invalidate_other_tokens(self):
        """Invalidate all other active tokens for this user"""
        PasswordReset.objects.filter(
            user=self.user,
            is_used=False
        ).exclude(id=self.id).update(is_used=True)

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
        RESET_REQUEST = 'reset_request', _('Password Reset Request')
        RESET_COMPLETE = 'reset_complete', _('Password Reset Complete')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs')
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auth_security_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} event for {self.user.email}"
