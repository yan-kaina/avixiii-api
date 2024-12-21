from django.test import TestCase, Client, override_settings
from django.utils import timezone
from datetime import timedelta
from graphene_django.utils.testing import GraphQLTestCase
from .models import Category, SourceCode, Purchase
import json
import shopify
from unittest.mock import patch, MagicMock

# Test settings
TEST_SETTINGS = {
    'SHOPIFY_SHOP_URL': 'test-store.myshopify.com',
    'SHOPIFY_ACCESS_TOKEN': 'test-token',
    'SHOPIFY_API_KEY': 'test-key',
    'SHOPIFY_API_SECRET': 'test-secret',
    'SHOPIFY_API_VERSION': '2024-01'
}

class CategoryModelTests(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(
            name="Web Development",
            description="Web development tools and templates"
        )
        self.assertEqual(category.slug, "web-development")
        self.assertTrue(isinstance(category, Category))
        self.assertEqual(str(category), "Web Development")

class SourceCodeModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Web Development",
            description="Web development tools and templates"
        )

    def test_source_code_creation(self):
        source_code = SourceCode.objects.create(
            title="E-commerce Platform",
            description="Complete e-commerce solution",
            category=self.category,
            price=99.99,
            shopify_product_id="123456",
            shopify_variant_id="789012",
            preview_image="https://example.com/image.jpg",
            features="Feature 1\nFeature 2",
            technologies="Django, React"
        )
        self.assertEqual(source_code.slug, "e-commerce-platform")
        self.assertTrue(isinstance(source_code, SourceCode))
        self.assertEqual(str(source_code), "E-commerce Platform")

class PurchaseModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Web Development")
        self.source_code = SourceCode.objects.create(
            title="E-commerce Platform",
            description="Complete e-commerce solution",
            category=self.category,
            price=99.99,
            shopify_product_id="123456",
            shopify_variant_id="789012",
            preview_image="https://example.com/image.jpg"
        )

    def test_purchase_creation(self):
        purchase = Purchase.objects.create(
            shopify_order_id="order_123",
            source_code=self.source_code,
            customer_email="test@example.com",
            download_expiry=timezone.now() + timedelta(days=30)
        )
        self.assertTrue(isinstance(purchase, Purchase))
        self.assertEqual(str(purchase), "test@example.com - E-commerce Platform")

@override_settings(**TEST_SETTINGS)
class GraphQLTests(GraphQLTestCase):
    GRAPHQL_URL = "/graphql/"

    def setUp(self):
        self.category = Category.objects.create(
            name="Web Development",
            description="Web development tools and templates"
        )
        self.source_code = SourceCode.objects.create(
            title="E-commerce Platform",
            description="Complete e-commerce solution",
            category=self.category,
            price=99.99,
            shopify_product_id="123456",
            shopify_variant_id="789012",
            preview_image="https://example.com/image.jpg",
            features="Feature 1\nFeature 2",
            technologies="Django, React"
        )

    def test_query_categories(self):
        response = self.query(
            '''
            query {
                categories {
                    id
                    name
                    slug
                    description
                }
            }
            '''
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertEqual(len(content['data']['categories']), 1)
        self.assertEqual(content['data']['categories'][0]['name'], "Web Development")

    def test_query_source_codes(self):
        response = self.query(
            '''
            query {
                sourceCodes {
                    id
                    title
                    slug
                    price
                    category {
                        name
                    }
                }
            }
            '''
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertEqual(len(content['data']['sourceCodes']), 1)
        self.assertEqual(content['data']['sourceCodes'][0]['title'], "E-commerce Platform")

    @patch('shopify.Session.setup')
    @patch('shopify.Session')
    @patch('shopify.ShopifyResource.activate_session')
    @patch('shopify.Checkout.create')
    def test_create_checkout_mutation(self, mock_create, mock_activate, mock_session, mock_setup):
        # Mock Shopify checkout response
        mock_checkout = MagicMock()
        mock_checkout.web_url = "https://checkout.shopify.com/123"
        mock_create.return_value = mock_checkout

        response = self.query(
            '''
            mutation {
                createCheckout(sourceCodeSlug: "e-commerce-platform") {
                    success
                    checkoutUrl
                    error
                }
            }
            '''
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertTrue(content['data']['createCheckout']['success'])
        self.assertEqual(
            content['data']['createCheckout']['checkoutUrl'],
            "https://checkout.shopify.com/123"
        )

class WebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Web Development")
        self.source_code = SourceCode.objects.create(
            title="E-commerce Platform",
            description="Complete e-commerce solution",
            category=self.category,
            price=99.99,
            shopify_product_id="123456",
            shopify_variant_id="789012",
            preview_image="https://example.com/image.jpg"
        )

    @patch('store.webhooks.verify_webhook')
    def test_order_webhook(self, mock_verify):
        mock_verify.return_value = True
        
        # Simulate Shopify order webhook
        webhook_data = {
            "id": "order_123",
            "email": "customer@example.com",
            "line_items": [{
                "variant_id": "789012",
                "quantity": 1
            }]
        }

        response = self.client.post(
            '/webhooks/order/',
            data=json.dumps(webhook_data),
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256='dummy_hmac'
        )

        self.assertEqual(response.status_code, 200)
        
        # Verify purchase was created
        purchase = Purchase.objects.get(shopify_order_id="order_123")
        self.assertEqual(purchase.customer_email, "customer@example.com")
        self.assertEqual(purchase.source_code, self.source_code)
