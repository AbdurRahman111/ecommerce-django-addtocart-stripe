from django.contrib import admin
from .models import Bag, BagItem


class BagAdmin(admin.ModelAdmin):
    list_display = (
        'bag_id',
        'date_added',
    )

class BagItemAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'bag',
        'quantity',
        'is_active',
    )

admin.site.register(Bag, BagAdmin)
admin.site.register(BagItem, BagItemAdmin)