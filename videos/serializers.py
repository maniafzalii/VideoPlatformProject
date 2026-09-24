from rest_framework import serializers
from .models import Category, Comment, Video, WatchHistory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class VideoListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    avg_rating = serializers.FloatField(read_only=True)
    ratings_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            'id', 'title', 'category', 'category_name', 'required_tier', 'views_count',
            'avg_rating', 'ratings_count', 'comments_count', 'is_locked', 'created_at',
        )

    def get_is_locked(self, obj):
        return self.context['user_tier'] < obj.required_tier


class VideoDetailSerializer(VideoListSerializer):
    class Meta(VideoListSerializer.Meta):
        fields = VideoListSerializer.Meta.fields + ('description', 'file_url')


class VideoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('id', 'title', 'description', 'file_url', 'required_tier', 'category')


class RatingInputSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=1, max_value=5)


class WatchInputSerializer(serializers.Serializer):
    progress_seconds = serializers.IntegerField(min_value=0, default=0)


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'user', 'body', 'created_at')
        read_only_fields = ('id', 'created_at')


class WatchHistorySerializer(serializers.ModelSerializer):
    video_title = serializers.CharField(source='video.title', read_only=True)

    class Meta:
        model = WatchHistory
        fields = ('id', 'video', 'video_title', 'progress_seconds', 'watched_at')