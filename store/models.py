from django.db import models
from django.utils.text import slugify
from django.conf import settings

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"

class SourceCode(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='source_codes')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    shopify_product_id = models.CharField(max_length=100, unique=True)
    shopify_variant_id = models.CharField(max_length=100, unique=True)
    github_repo_url = models.URLField(blank=True)
    preview_image = models.URLField()
    demo_url = models.URLField(blank=True)
    features = models.TextField()
    technologies = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Purchase(models.Model):
    shopify_order_id = models.CharField(max_length=100, unique=True)
    source_code = models.ForeignKey(SourceCode, on_delete=models.PROTECT)
    customer_email = models.EmailField()
    purchase_date = models.DateTimeField(auto_now_add=True)
    download_count = models.IntegerField(default=0)
    download_expiry = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.customer_email} - {self.source_code.title}"
