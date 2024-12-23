from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from .models import Profile, Address, Notification, NotificationPreference

User = get_user_model()

class ProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile_data = {
            'user': self.user,
            'bio': 'Test bio',
            'phone_number': '+1234567890',
            'website': 'https://example.com',
            'company': 'Test Company',
            'position': 'Test Position'
        }

    def test_profile_creation(self):
        """Test creating a profile with valid data"""
        profile = Profile.objects.create(**self.profile_data)
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, self.profile_data['bio'])
        self.assertEqual(profile.phone_number, self.profile_data['phone_number'])

    def test_invalid_phone_number(self):
        """Test profile creation with invalid phone number"""
        with self.assertRaises(ValidationError):
            profile = Profile(
                user=self.user,
                phone_number='invalid-phone'
            )
            profile.full_clean()

    def test_invalid_website(self):
        """Test profile creation with invalid website"""
        with self.assertRaises(ValidationError):
            profile = Profile(
                user=self.user,
                website='invalid-url'
            )
            profile.full_clean()

    def test_profile_caching(self):
        """Test profile caching functionality"""
        profile = Profile.objects.create(**self.profile_data)
        cache_key = profile.get_cache_key()
        
        # Create cache entry
        cache.set(cache_key, profile)
        
        # Verify cache is cleared on save
        profile.bio = 'Updated bio'
        profile.save()
        
        self.assertIsNone(cache.get(cache_key))

class AddressTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.address_data = {
            'user': self.user,
            'type': Address.AddressType.SHIPPING,
            'full_name': 'Test User',
            'phone_number': '+1234567890',
            'street_address': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'postal_code': '12345',
            'country': 'Test Country'
        }

    def test_address_creation(self):
        """Test creating an address with valid data"""
        address = Address.objects.create(**self.address_data)
        
        self.assertEqual(address.user, self.user)
        self.assertEqual(address.type, Address.AddressType.SHIPPING)
        self.assertEqual(address.full_name, self.address_data['full_name'])

    def test_default_address(self):
        """Test default address functionality"""
        # Create first address as default
        address1 = Address.objects.create(
            **self.address_data,
            is_default=True
        )
        
        # Create second address as default
        address2 = Address.objects.create(
            **self.address_data,
            is_default=True
        )
        
        # Refresh from database
        address1.refresh_from_db()
        address2.refresh_from_db()
        
        # First address should no longer be default
        self.assertFalse(address1.is_default)
        self.assertTrue(address2.is_default)

    def test_address_types(self):
        """Test different address types"""
        shipping = Address.objects.create(**self.address_data)
        
        billing_data = self.address_data.copy()
        billing_data['type'] = Address.AddressType.BILLING
        billing = Address.objects.create(**billing_data)
        
        self.assertEqual(shipping.type, Address.AddressType.SHIPPING)
        self.assertEqual(billing.type, Address.AddressType.BILLING)

class NotificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.notification_data = {
            'user': self.user,
            'type': Notification.NotificationType.EMAIL,
            'title': 'Test Notification',
            'message': 'Test message',
            'data': {'test_key': 'test_value'}
        }

    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.objects.create(**self.notification_data)
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, self.notification_data['title'])
        self.assertEqual(notification.type, Notification.NotificationType.EMAIL)
        self.assertFalse(notification.is_read)

    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(**self.notification_data)
        
        # Mark as read
        notification.mark_as_read()
        notification.refresh_from_db()
        
        self.assertTrue(notification.is_read)

class NotificationPreferenceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_preference_creation(self):
        """Test creating notification preferences"""
        prefs = NotificationPreference.objects.create(user=self.user)
        
        # Test default values
        self.assertTrue(prefs.email_notifications)
        self.assertFalse(prefs.sms_notifications)
        self.assertTrue(prefs.push_notifications)
        self.assertTrue(prefs.newsletter)
        self.assertTrue(prefs.security_alerts)

    def test_preference_update(self):
        """Test updating notification preferences"""
        prefs = NotificationPreference.objects.create(user=self.user)
        
        # Update preferences
        prefs.email_notifications = False
        prefs.sms_notifications = True
        prefs.save()
        
        # Refresh from database
        prefs.refresh_from_db()
        
        self.assertFalse(prefs.email_notifications)
        self.assertTrue(prefs.sms_notifications)

    def test_preference_caching(self):
        """Test preference caching functionality"""
        prefs = NotificationPreference.objects.create(user=self.user)
        cache_key = prefs.get_cache_key()
        
        # Create cache entry
        cache.set(cache_key, prefs)
        
        # Verify cache is cleared on save
        prefs.email_notifications = False
        prefs.save()
        
        self.assertIsNone(cache.get(cache_key))
