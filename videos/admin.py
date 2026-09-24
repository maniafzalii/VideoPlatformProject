from django.contrib import admin
from .models import Category, Comment, Rating, Video, WatchHistory


admin.site.register(Category)
admin.site.register(Rating)
admin.site.register(Comment)
admin.site.register(WatchHistory)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'required_tier', 'views_count', 'category')
    list_filter = ('required_tier', 'category')
    search_fields = ('title',)

