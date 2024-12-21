import graphene
from graphene_django import DjangoObjectType
from .models import Category, SourceCode, Purchase
from django.core.exceptions import ObjectDoesNotExist
import shopify

class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = "__all__"

class SourceCodeType(DjangoObjectType):
    class Meta:
        model = SourceCode
        fields = "__all__"

class PurchaseType(DjangoObjectType):
    class Meta:
        model = Purchase
        fields = "__all__"

class Query(graphene.ObjectType):
    categories = graphene.List(CategoryType)
    category = graphene.Field(CategoryType, slug=graphene.String(required=True))
    source_codes = graphene.List(SourceCodeType, category_slug=graphene.String())
    source_code = graphene.Field(SourceCodeType, slug=graphene.String(required=True))
    my_purchases = graphene.List(PurchaseType, email=graphene.String(required=True))

    def resolve_categories(self, info):
        return Category.objects.all()

    def resolve_category(self, info, slug):
        try:
            return Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            return None

    def resolve_source_codes(self, info, category_slug=None):
        queryset = SourceCode.objects.filter(is_active=True)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    def resolve_source_code(self, info, slug):
        try:
            return SourceCode.objects.get(slug=slug, is_active=True)
        except SourceCode.DoesNotExist:
            return None

    def resolve_my_purchases(self, info, email):
        return Purchase.objects.filter(customer_email=email, is_active=True)

class CreateCheckoutMutation(graphene.Mutation):
    class Arguments:
        source_code_slug = graphene.String(required=True)

    checkout_url = graphene.String()
    success = graphene.Boolean()
    error = graphene.String()

    def mutate(self, info, source_code_slug):
        try:
            source_code = SourceCode.objects.get(slug=source_code_slug, is_active=True)
            
            # Initialize Shopify session
            shopify.Session.setup(api_key=settings.SHOPIFY_API_KEY, secret=settings.SHOPIFY_API_SECRET)
            session = shopify.Session(settings.SHOPIFY_SHOP_URL, settings.SHOPIFY_API_VERSION, settings.SHOPIFY_ACCESS_TOKEN)
            shopify.ShopifyResource.activate_session(session)

            # Create checkout
            checkout = shopify.Checkout.create({
                "line_items": [{
                    "variant_id": source_code.shopify_variant_id,
                    "quantity": 1
                }],
                "custom_attributes": [{
                    "key": "source_code_slug",
                    "value": source_code_slug
                }]
            })

            shopify.ShopifyResource.clear_session()
            
            return CreateCheckoutMutation(
                success=True,
                checkout_url=checkout.web_url,
                error=None
            )

        except ObjectDoesNotExist:
            return CreateCheckoutMutation(success=False, error="Source code not found")
        except Exception as e:
            return CreateCheckoutMutation(success=False, error=str(e))

class Mutation(graphene.ObjectType):
    create_checkout = CreateCheckoutMutation.Field()
