from django.contrib import admin

from marketplace.models import *
from .models import *


# Register your models here.

class CatalogAdmin(admin.ModelAdmin):
    list_display = ['repository_id', 'VNF_name', 'developer', 'institution', 'category']
    search_fields = ['developer', 'institution', 'category']
    list_filter = ['developer', 'institution', 'category']


admin.site.register(Request)
admin.site.register(Acquisitions)
admin.site.register(Catalog, CatalogAdmin)
admin.site.register(Version)
admin.site.register(Permission)
admin.site.register(RequestVNFD)
admin.site.register(Category)
admin.site.register(TAG)
admin.site.register(Instance)
admin.site.register(SFC)
admin.site.register(SFCStatus)
admin.site.register(Status)
admin.site.register(Infrastructure)
admin.site.register(Catalog_SFC)
admin.site.register(Print)
