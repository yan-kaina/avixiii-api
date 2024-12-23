from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from datetime import timedelta
from .models import LoginAttempt, PasswordReset, SecurityLog, UserRole

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'role': UserRole.CUSTOMER
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_creation(self):
        """Test user creation with valid data"""
        self.assertEqual(self.user.username, self.user_data['username'])
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertEqual(self.user.role, UserRole.CUSTOMER)
        self.assertFalse(self.user.is_email_verified)

    def test_invalid_email(self):
        """Test user creation with invalid email"""
        with self.assertRaises(ValidationError):
            user = User(
                username='testuser2',
                email='invalid-email',
                password='testpass123',
                role=UserRole.CUSTOMER
            )
            user.full_clean()

    def test_user_roles(self):
        """Test user role properties"""
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role=UserRole.ADMIN
        )
        staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staff123',
            role=UserRole.STAFF
        )

        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_staff_member)
        self.assertTrue(staff.is_staff_member)
        self.assertFalse(staff.is_customer)
        self.assertTrue(self.user.is_customer)

    def test_failed_login_attempts(self):
        """Test failed login attempts and account locking"""
        self.assertEqual(self.user.failed_login_attempts, 0)
        
        # Test incrementing failed attempts
        for _ in range(4):
            self.user.increment_failed_login()
            self.user.refresh_from_db()
        
        self.assertEqual(self.user.failed_login_attempts, 4)
        self.assertFalse(self.user.is_account_locked())

        # Test account locking after 5 attempts
        self.user.increment_failed_login()
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.failed_login_attempts, 5)
        self.assertTrue(self.user.is_account_locked())

        # Test reset failed attempts
        self.user.reset_failed_login()
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertFalse(self.user.is_account_locked())

class LoginAttemptTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.ip_address = '127.0.0.1'

    def test_login_attempt_creation(self):
        """Test creating login attempt records"""
        attempt = LoginAttempt.objects.create(
            user=self.user,
            ip_address=self.ip_address,
            user_agent='Mozilla/5.0',
            success=True
        )
        
        self.assertEqual(attempt.user, self.user)
        self.assertEqual(attempt.ip_address, self.ip_address)
        self.assertTrue(attempt.success)

    def test_ip_rate_limiting(self):
        """Test IP-based rate limiting"""
        # Clear any existing cache
        cache.clear()
        
        # Test successful rate limiting
        for _ in range(9):
            self.assertTrue(LoginAttempt.check_ip_rate_limit(self.ip_address))
        
        # Test rate limit exceeded
        self.assertTrue(LoginAttempt.check_ip_rate_limit(self.ip_address))  # 10th attempt
        self.assertFalse(LoginAttempt.check_ip_rate_limit(self.ip_address))  # 11th attempt

class PasswordResetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_password_reset_token(self):
        """Test password reset token creation and validation"""
        reset = PasswordReset.objects.create(
            user=self.user,
            token='testtoken123',
            expires_at=timezone.now() + timedelta(hours=24),
            created_ip='127.0.0.1'
        )
        
        self.assertFalse(reset.is_used)
        self.assertFalse(reset.is_expired)

        # Test expiration
        reset.expires_at = timezone.now() - timedelta(hours=1)
        self.assertTrue(reset.is_expired)

    def test_invalidate_other_tokens(self):
        """Test invalidating previous tokens"""
        # Create multiple tokens
        token1 = PasswordReset.objects.create(
            user=self.user,
            token='token1',
            expires_at=timezone.now() + timedelta(hours=24),
            created_ip='127.0.0.1'
        )
        token2 = PasswordReset.objects.create(
            user=self.user,
            token='token2',
            expires_at=timezone.now() + timedelta(hours=24),
            created_ip='127.0.0.1'
        )
        
        # Invalidate previous tokens
        token2.invalidate_other_tokens()
        
        token1.refresh_from_db()
        self.assertTrue(token1.is_used)
        self.assertFalse(token2.is_used)

class SecurityLogTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_security_log_creation(self):
        """Test creating security log entries"""
        log = SecurityLog.objects.create(
            user=self.user,
            event_type=SecurityLog.EventType.PASSWORD_CHANGE,
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0',
            details={'old_password': 'hashed_old_pass'}
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.event_type, SecurityLog.EventType.PASSWORD_CHANGE)
        self.assertEqual(log.ip_address, '127.0.0.1')
        self.assertTrue('old_password' in log.details)
