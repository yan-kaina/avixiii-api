from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, URLValidator
from django.core.cache import cache

class Profile(models.Model):
    """
    Extended profile information for users
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        null=True,
        blank=True,
        help_text=_('User profile picture')
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text=_('A brief description about yourself')
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text=_('Your date of birth')
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text=_('Contact phone number')
    )
    website = models.URLField(
        max_length=200,
        blank=True,
        validators=[URLValidator()],
        help_text=_('Your personal or business website')
    )
    company = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Company you work for')
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Your job position')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['phone_number']),
        ]
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_cache_key(self):
        return f'profile_{self.user_id}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete(self.get_cache_key())

class Address(models.Model):
    """
    User addresses for shipping/billing
    """
    class AddressType(models.TextChoices):
        SHIPPING = 'shipping', _('Shipping')
        BILLING = 'billing', _('Billing')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    type = models.CharField(
        max_length=10,
        choices=AddressType.choices,
        default=AddressType.SHIPPING,
        db_index=True
    )
    is_default = models.BooleanField(default=False)
    full_name = models.CharField(
        max_length=100,
        help_text=_('Full name of the recipient')
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        help_text=_('Contact phone number')
    )
    street_address = models.CharField(
        max_length=255,
        help_text=_('Street address')
    )
    apartment = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Apartment, suite, unit, etc.')
    )
    city = models.CharField(
        max_length=100,
        help_text=_('City')
    )
    state = models.CharField(
        max_length=100,
        help_text=_('State/Province/Region')
    )
    postal_code = models.CharField(
        max_length=20,
        help_text=_('Postal/ZIP code')
    )
    country = models.CharField(
        max_length=100,
        help_text=_('Country')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'addresses'
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'type', '-is_default']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username}'s {self.get_type_display()} address"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default address per type per user
            Address.objects.filter(
                user=self.user,
                type=self.type,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)
        # Clear cache
        cache.delete(f'addresses_{self.user_id}')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        # Clear cache
        cache.delete(f'addresses_{self.user_id}')

class Notification(models.Model):
    """
    User notifications system
    """
    class NotificationType(models.TextChoices):
        EMAIL = 'email', _('Email')
        SMS = 'sms', _('SMS')
        PUSH = 'push', _('Push Notification')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type = models.CharField(
        max_length=10,
        choices=NotificationType.choices,
        db_index=True
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    data = models.JSONField(
        default=dict,
        help_text=_('Additional data for the notification')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} for {self.user.username}"

    def mark_as_read(self):
        """Mark notification as read and clear cache"""
        self.is_read = True
        self.save()
        cache.delete(f'unread_notifications_{self.user_id}')

class NotificationPreference(models.Model):
    """
    User preferences for different types of notifications
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    email_notifications = models.BooleanField(
        default=True,
        help_text=_('Receive email notifications')
    )
    sms_notifications = models.BooleanField(
        default=False,
        help_text=_('Receive SMS notifications')
    )
    push_notifications = models.BooleanField(
        default=True,
        help_text=_('Receive push notifications')
    )
    newsletter = models.BooleanField(
        default=True,
        help_text=_('Receive newsletter')
    )
    marketing_emails = models.BooleanField(
        default=False,
        help_text=_('Receive marketing emails')
    )
    order_updates = models.BooleanField(
        default=True,
        help_text=_('Receive order status updates')
    )
    security_alerts = models.BooleanField(
        default=True,
        help_text=_('Receive security alerts')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username}'s notification preferences"

    def get_cache_key(self):
        return f'notification_preferences_{self.user_id}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete(self.get_cache_key())
