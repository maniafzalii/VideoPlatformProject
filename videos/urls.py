from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, VideoViewSet, WatchHistoryListView

router = DefaultRouter()
router.register('videos', VideoViewSet, basename='video')
router.register('categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('history/', WatchHistoryListView.as_view(), name='watch-history'),
    path('', include(router.urls)),
]
