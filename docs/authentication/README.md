# Authentication System Documentation

## Overview
The authentication system provides a secure and flexible way to manage user authentication, authorization, and security features. It includes user management, login attempt tracking, password reset functionality, and security logging.

## Models

### User Model
The custom User model extends Django's AbstractUser and adds additional fields and functionality.

#### Fields
- `email`: Unique email address with validation
- `role`: User role (ADMIN, STAFF, CUSTOMER)
- `is_email_verified`: Boolean indicating email verification status
- `last_login_ip`: IP address of last login
- `failed_login_attempts`: Counter for failed login attempts
- `last_failed_login`: Timestamp of last failed login
- `account_locked_until`: Timestamp until account is locked

#### Methods
- `increment_failed_login()`: Increment failed login attempts and handle account locking
- `reset_failed_login()`: Reset failed login attempts counter
- `is_account_locked()`: Check if account is currently locked
- `is_admin`, `is_staff_member`, `is_customer`: Role check properties

### LoginAttempt Model
Tracks login attempts for security monitoring and rate limiting.

#### Fields
- `user`: ForeignKey to User model
- `ip_address`: IP address of login attempt
- `user_agent`: User agent string
- `success`: Boolean indicating success/failure
- `timestamp`: When the attempt occurred
- `failure_reason`: Optional reason for failure

#### Methods
- `check_ip_rate_limit(ip_address)`: Check if IP has exceeded rate limit (10 attempts per minute)

### PasswordReset Model
Manages password reset tokens and their lifecycle.

#### Fields
- `user`: ForeignKey to User model
- `token`: Unique reset token
- `is_used`: Boolean indicating if token was used
- `expires_at`: Token expiration timestamp
- `created_at`: Token creation timestamp
- `used_at`: When token was used
- `created_ip`: IP address that requested reset

#### Methods
- `is_expired`: Check if token has expired
- `invalidate_other_tokens()`: Invalidate all other active tokens for user

### SecurityLog Model
Logs security-related events for audit purposes.

#### Fields
- `user`: ForeignKey to User model
- `event_type`: Type of security event
- `ip_address`: IP address associated with event
- `user_agent`: User agent string
- `details`: JSON field for additional event details
- `created_at`: Event timestamp

#### Event Types
- PASSWORD_CHANGE
- EMAIL_CHANGE
- ROLE_CHANGE
- ACCOUNT_LOCK
- ACCOUNT_UNLOCK
- LOGIN_SUCCESS
- LOGIN_FAILURE
- RESET_REQUEST
- RESET_COMPLETE

## Security Features

### Account Protection
1. **Rate Limiting**
   - IP-based rate limiting (10 attempts per minute)
   - Account locking after 5 failed attempts
   - 30-minute lockout period

2. **Password Security**
   - Secure password reset flow
   - Token expiration
   - Previous token invalidation

3. **Audit Trail**
   - Comprehensive security logging
   - IP address tracking
   - User agent tracking

### Best Practices
1. Always use HTTPS in production
2. Implement proper CORS settings
3. Use environment variables for sensitive settings
4. Regularly review security logs
5. Set up monitoring for suspicious activity

## Testing
Run the test suite:
```bash
python manage.py test authentication
```

Test coverage includes:
- User creation and validation
- Login attempt tracking
- Password reset functionality
- Security logging
- Rate limiting
- Account locking
