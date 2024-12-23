import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from graphql import GraphQLError
from django.core.exceptions import ValidationError
from .models import Profile, Address, Notification, NotificationPreference

# Types
class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile
        fields = '__all__'

class AddressType(DjangoObjectType):
    class Meta:
        model = Address
        fields = '__all__'

class NotificationType(DjangoObjectType):
    class Meta:
        model = Notification
        fields = '__all__'

class NotificationPreferenceType(DjangoObjectType):
    class Meta:
        model = NotificationPreference
        fields = '__all__'

# Profile Mutations
class UpdateProfile(graphene.Mutation):
    class Arguments:
        bio = graphene.String()
        date_of_birth = graphene.Date()
        phone_number = graphene.String()
        website = graphene.String()
        company = graphene.String()
        position = graphene.String()

    profile = graphene.Field(ProfileType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        profile, created = Profile.objects.get_or_create(user=user)
        
        for field, value in kwargs.items():
            if value is not None:
                setattr(profile, field, value)
        
        try:
            profile.save()
            return UpdateProfile(
                profile=profile,
                success=True,
                message="Profile updated successfully"
            )
        except Exception as e:
            return UpdateProfile(success=False, message=str(e))

# Address Mutations
class CreateAddress(graphene.Mutation):
    class Arguments:
        type = graphene.String(required=True)
        is_default = graphene.Boolean()
        full_name = graphene.String(required=True)
        phone_number = graphene.String(required=True)
        street_address = graphene.String(required=True)
        apartment = graphene.String()
        city = graphene.String(required=True)
        state = graphene.String(required=True)
        postal_code = graphene.String(required=True)
        country = graphene.String(required=True)

    address = graphene.Field(AddressType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        try:
            address = Address.objects.create(user=user, **kwargs)
            return CreateAddress(
                address=address,
                success=True,
                message="Address created successfully"
            )
        except Exception as e:
            return CreateAddress(success=False, message=str(e))

class UpdateAddress(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        is_default = graphene.Boolean()
        full_name = graphene.String()
        phone_number = graphene.String()
        street_address = graphene.String()
        apartment = graphene.String()
        city = graphene.String()
        state = graphene.String()
        postal_code = graphene.String()
        country = graphene.String()

    address = graphene.Field(AddressType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info, id, **kwargs):
        try:
            address = Address.objects.get(id=id, user=info.context.user)
            for field, value in kwargs.items():
                if value is not None:
                    setattr(address, field, value)
            address.save()
            return UpdateAddress(
                address=address,
                success=True,
                message="Address updated successfully"
            )
        except Address.DoesNotExist:
            return UpdateAddress(success=False, message="Address not found")
        except Exception as e:
            return UpdateAddress(success=False, message=str(e))

class DeleteAddress(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info, id):
        try:
            address = Address.objects.get(id=id, user=info.context.user)
            address.delete()
            return DeleteAddress(success=True, message="Address deleted successfully")
        except Address.DoesNotExist:
            return DeleteAddress(success=False, message="Address not found")

# Notification Mutations
class UpdateNotificationPreferences(graphene.Mutation):
    class Arguments:
        email_notifications = graphene.Boolean()
        sms_notifications = graphene.Boolean()
        push_notifications = graphene.Boolean()
        newsletter = graphene.Boolean()
        marketing_emails = graphene.Boolean()
        order_updates = graphene.Boolean()
        security_alerts = graphene.Boolean()

    preferences = graphene.Field(NotificationPreferenceType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        preferences, created = NotificationPreference.objects.get_or_create(user=user)
        
        for field, value in kwargs.items():
            if value is not None:
                setattr(preferences, field, value)
        
        try:
            preferences.save()
            return UpdateNotificationPreferences(
                preferences=preferences,
                success=True,
                message="Notification preferences updated successfully"
            )
        except Exception as e:
            return UpdateNotificationPreferences(success=False, message=str(e))

class MarkNotificationAsRead(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    notification = graphene.Field(NotificationType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info, id):
        try:
            notification = Notification.objects.get(id=id, user=info.context.user)
            notification.is_read = True
            notification.save()
            return MarkNotificationAsRead(
                notification=notification,
                success=True,
                message="Notification marked as read"
            )
        except Notification.DoesNotExist:
            return MarkNotificationAsRead(success=False, message="Notification not found")

# Queries
class Query(graphene.ObjectType):
    profile = graphene.Field(ProfileType)
    addresses = graphene.List(AddressType)
    address = graphene.Field(AddressType, id=graphene.ID(required=True))
    notifications = graphene.List(
        NotificationType,
        is_read=graphene.Boolean(),
        limit=graphene.Int()
    )
    notification_preferences = graphene.Field(NotificationPreferenceType)

    @login_required
    def resolve_profile(self, info):
        return Profile.objects.get_or_create(user=info.context.user)[0]

    @login_required
    def resolve_addresses(self, info):
        return Address.objects.filter(user=info.context.user)

    @login_required
    def resolve_address(self, info, id):
        try:
            return Address.objects.get(id=id, user=info.context.user)
        except Address.DoesNotExist:
            raise GraphQLError('Address not found')

    @login_required
    def resolve_notifications(self, info, is_read=None, limit=None):
        notifications = Notification.objects.filter(user=info.context.user)
        if is_read is not None:
            notifications = notifications.filter(is_read=is_read)
        if limit:
            notifications = notifications[:limit]
        return notifications

    @login_required
    def resolve_notification_preferences(self, info):
        return NotificationPreference.objects.get_or_create(user=info.context.user)[0]

class Mutation(graphene.ObjectType):
    update_profile = UpdateProfile.Field()
    create_address = CreateAddress.Field()
    update_address = UpdateAddress.Field()
    delete_address = DeleteAddress.Field()
    update_notification_preferences = UpdateNotificationPreferences.Field()
    mark_notification_as_read = MarkNotificationAsRead.Field()
