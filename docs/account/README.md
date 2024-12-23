# Account Management System Documentation

## Overview
The account management system provides comprehensive user profile management, address handling, and notification features. It's designed to be flexible, scalable, and integrated with the authentication system.

## Models

### Profile Model
Extended user profile information storage.

#### Fields
- `user`: OneToOneField to User model
- `avatar`: User profile picture (stored in avatars/%Y/%m/)
- `bio`: User biography text
- `date_of_birth`: User's birth date
- `phone_number`: Validated phone number
- `website`: Validated URL
- `company`: Company name
- `position`: Job position

#### Features
- Phone number validation with regex
- Website URL validation
- Profile caching for performance
- Automatic cache invalidation on updates

### Address Model
Manages user shipping and billing addresses.

#### Fields
- `user`: ForeignKey to User model
- `type`: Address type (SHIPPING/BILLING)
- `is_default`: Default address flag
- `full_name`: Recipient's full name
- `phone_number`: Contact phone number
- `street_address`: Street address
- `apartment`: Optional apartment/suite
- `city`: City name
- `state`: State/Province
- `postal_code`: Postal/ZIP code
- `country`: Country name

#### Features
- Multiple address support per user
- Default address management
- Address type categorization
- Automatic cache clearing

### Notification Model
User notification system.

#### Fields
- `user`: ForeignKey to User model
- `type`: Notification type (EMAIL/SMS/PUSH)
- `title`: Notification title
- `message`: Notification content
- `is_read`: Read status
- `data`: Additional JSON data
- `created_at`: Creation timestamp

#### Features
- Multiple notification types
- Read status tracking
- Additional data storage
- Automatic ordering by creation time

### NotificationPreference Model
User notification preferences management.

#### Fields
- `user`: OneToOneField to User model
- `email_notifications`: Email notifications flag
- `sms_notifications`: SMS notifications flag
- `push_notifications`: Push notifications flag
- `newsletter`: Newsletter subscription
- `marketing_emails`: Marketing email preference
- `order_updates`: Order update notifications
- `security_alerts`: Security notification preference

#### Features
- Granular notification control
- Default preferences
- Preference caching
- Automatic cache invalidation

## Performance Optimizations

### Database Indexes
- User-based indexes for quick lookups
- Type-based indexes for filtering
- Timestamp-based indexes for ordering
- Compound indexes for common queries

### Caching Strategy
1. **Profile Caching**
   - Cache key: `profile_{user_id}`
   - Invalidated on profile updates

2. **Address Caching**
   - Cache key: `addresses_{user_id}`
   - Invalidated on address changes

3. **Notification Preferences**
   - Cache key: `notification_preferences_{user_id}`
   - Invalidated on preference updates

## Validation

### Phone Numbers
- International format support
- Regex validation: `^\+?1?\d{9,15}$`
- Helpful error messages

### URLs
- Standard URL validation
- Protocol requirement
- Domain validation

## Testing
Run the test suite:
```bash
python manage.py test account
```

Test coverage includes:
- Profile creation and validation
- Address management
- Notification system
- Preference handling
- Caching functionality
- Field validation

## Best Practices

### Profile Management
1. Use appropriate image formats for avatars
2. Implement image size limits
3. Consider implementing image cropping
4. Validate and sanitize user input

### Address Management
1. Implement address verification
2. Consider using address normalization
3. Support international formats
4. Maintain address history

### Notification System
1. Implement notification batching
2. Set up notification queues
3. Handle notification failures
4. Implement read receipt tracking

## API Integration
The account system integrates with the authentication system and provides GraphQL endpoints for:
- Profile management
- Address CRUD operations
- Notification handling
- Preference management
