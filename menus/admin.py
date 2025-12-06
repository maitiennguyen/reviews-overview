from django.contrib import admin
from .models import Place, MenuItem, Review, MenuItemReviewMention, MenuItemReviewSummary

admin.site.register(Place)
admin.site.register(MenuItem)
admin.site.register(Review)
admin.site.register(MenuItemReviewMention)
admin.site.register(MenuItemReviewSummary)
