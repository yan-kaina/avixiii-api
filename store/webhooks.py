import hmac
import hashlib
import base64
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import SourceCode, Purchase

def verify_webhook(data, hmac_header):
    digest = hmac.new(
        settings.SHOPIFY_API_SECRET.encode('utf-8'),
        data,
        hashlib.sha256
    ).digest()
    computed_hmac = base64.b64encode(digest).decode('utf-8')
    return hmac.compare_digest(computed_hmac, hmac_header)

@csrf_exempt
@require_POST
def order_webhook(request):
    # Verify webhook
    hmac_header = request.headers.get('X-Shopify-Hmac-SHA256')
    if not hmac_header or not verify_webhook(request.body, hmac_header):
        return HttpResponse(status=401)

    try:
        # Parse order data
        order_data = json.loads(request.body)
        
        # Process each line item
        for item in order_data['line_items']:
            # Find source code by Shopify variant ID
            try:
                source_code = SourceCode.objects.get(shopify_variant_id=item['variant_id'])
                
                # Create purchase record
                Purchase.objects.create(
                    shopify_order_id=order_data['id'],
                    source_code=source_code,
                    customer_email=order_data['email'],
                    download_expiry=datetime.now() + timedelta(days=30)  # 30 days download window
                )
            except SourceCode.DoesNotExist:
                continue  # Skip if source code not found

        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(status=500)
