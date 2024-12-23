import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from graphql_jwt.decorators import login_required, staff_member_required, superuser_required
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from graphql import GraphQLError
import graphql_jwt
from datetime import datetime
from .models import LoginAttempt, PasswordReset, SecurityLog, UserRole

# Types
class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'is_email_verified', 'date_joined', 'last_login',
                 'created_at', 'updated_at')

class LoginAttemptType(DjangoObjectType):
    class Meta:
        model = LoginAttempt
        fields = ('id', 'user', 'ip_address', 'user_agent', 'success', 
                 'timestamp', 'failure_reason')

class SecurityLogType(DjangoObjectType):
    class Meta:
        model = SecurityLog
        fields = ('id', 'user', 'event_type', 'ip_address', 'user_agent', 
                 'details', 'created_at')

# Mutations
class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        role = graphene.String()

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, username, email, password, first_name=None, 
               last_name=None, role=None):
        User = get_user_model()

        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            return CreateUser(success=False, message=str(e))

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            return CreateUser(success=False, message="Username already exists")
        if User.objects.filter(email=email).exists():
            return CreateUser(success=False, message="Email already exists")

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name or "",
                last_name=last_name or "",
                role=role or UserRole.CUSTOMER
            )
            return CreateUser(user=user, success=True, 
                            message="User created successfully")
        except Exception as e:
            return CreateUser(success=False, message=str(e))

class UpdateUser(graphene.Mutation):
    class Arguments:
        first_name = graphene.String()
        last_name = graphene.String()
        email = graphene.String()

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        try:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(user, key, value)
            user.save()
            return UpdateUser(user=user, success=True, 
                            message="User updated successfully")
        except Exception as e:
            return UpdateUser(success=False, message=str(e))

class ChangePassword(graphene.Mutation):
    class Arguments:
        old_password = graphene.String(required=True)
        new_password = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info, old_password, new_password):
        user = info.context.user
        if not user.check_password(old_password):
            return ChangePassword(success=False, 
                                message="Old password is incorrect")

        try:
            validate_password(new_password)
            user.set_password(new_password)
            user.save()

            # Log the password change
            SecurityLog.objects.create(
                user=user,
                event_type=SecurityLog.EventType.PASSWORD_CHANGE,
                ip_address=info.context.META.get('REMOTE_ADDR'),
                user_agent=info.context.META.get('HTTP_USER_AGENT', ''),
                details={'source': 'user_initiated'}
            )

            return ChangePassword(success=True, 
                                message="Password changed successfully")
        except ValidationError as e:
            return ChangePassword(success=False, message=str(e))
        except Exception as e:
            return ChangePassword(success=False, message=str(e))

class RequestPasswordReset(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, email):
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            # Implementation of password reset token creation and email sending
            # would go here
            return RequestPasswordReset(success=True, 
                message="Password reset instructions sent to your email")
        except User.DoesNotExist:
            return RequestPasswordReset(success=True, 
                message="If an account exists with this email, "
                       "you will receive password reset instructions.")

# Queries
class Query(graphene.ObjectType):
    me = graphene.Field(UserType)
    user = graphene.Field(UserType, id=graphene.ID())
    users = graphene.List(UserType)
    login_attempts = graphene.List(LoginAttemptType)
    security_logs = graphene.List(SecurityLogType)

    @login_required
    def resolve_me(self, info):
        return info.context.user

    @staff_member_required
    def resolve_user(self, info, id):
        User = get_user_model()
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            raise GraphQLError('User not found')

    @staff_member_required
    def resolve_users(self, info):
        return get_user_model().objects.all()

    @login_required
    def resolve_login_attempts(self, info):
        return LoginAttempt.objects.filter(user=info.context.user)

    @login_required
    def resolve_security_logs(self, info):
        return SecurityLog.objects.filter(user=info.context.user)

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    change_password = ChangePassword.Field()
    request_password_reset = RequestPasswordReset.Field()

    # JWT mutations
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    revoke_token = graphql_jwt.Revoke.Field()
