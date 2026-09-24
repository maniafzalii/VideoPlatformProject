from django.db.models import Avg, Count, F
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from subscriptions.services import get_user_tier
from .events import broadcast_video_event
from .models import Category, Rating, Video, WatchHistory
from .permissions import HasRequiredTier, IsAdminOrReadOnly
from .serializers import (
    CategorySerializer, CommentSerializer, RatingInputSerializer, VideoDetailSerializer,
    VideoListSerializer, VideoWriteSerializer, WatchHistorySerializer, WatchInputSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class VideoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly, HasRequiredTier]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'views_count', 'avg_rating']

    def get_queryset(self):
        qs = Video.objects.select_related('category').annotate(
            avg_rating=Avg('ratings__score'),
            ratings_count=Count('ratings', distinct=True),
            comments_count=Count('comments', distinct=True),
        )
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category_id=category)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return VideoListSerializer
        if self.action == 'retrieve':
            return VideoDetailSerializer
        return VideoWriteSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_tier'] = get_user_tier(self.request.user)
        return context

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, HasRequiredTier])
    def watch(self, request, pk=None):
        video = self.get_object()
        serializer = WatchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        WatchHistory.objects.update_or_create(
            user=request.user, video=video,
            defaults={'progress_seconds': serializer.validated_data['progress_seconds']},
        )
        Video.objects.filter(pk=video.pk).update(views_count=F('views_count') + 1)
        video.refresh_from_db()

        broadcast_video_event(video.pk, 'view', {'views_count': video.views_count})
        return Response({'file_url': video.file_url, 'views_count': video.views_count})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, HasRequiredTier])
    def rate(self, request, pk=None):
        video = self.get_object()
        serializer = RatingInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        Rating.objects.update_or_create(
            user=request.user, video=video,
            defaults={'score': serializer.validated_data['score']},
        )
        stats = video.ratings.aggregate(avg_rating=Avg('score'), ratings_count=Count('id'))
        broadcast_video_event(video.pk, 'rating', stats)
        return Response(stats)

    @action(
        detail=True, methods=['get', 'post'], url_path='comments',
        permission_classes=[IsAuthenticated, HasRequiredTier],
    )
    def comments(self, request, pk=None):
        video = self.get_object()

        if request.method == 'GET':
            page = self.paginate_queryset(video.comments.select_related('user'))
            return self.get_paginated_response(CommentSerializer(page, many=True).data)

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(user=request.user, video=video)
        broadcast_video_event(video.pk, 'comment', dict(CommentSerializer(comment).data))
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WatchHistoryListView(generics.ListAPIView):
    serializer_class = WatchHistorySerializer

    def get_queryset(self):
        return WatchHistory.objects.filter(user=self.request.user).select_related('video')