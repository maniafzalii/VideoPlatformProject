from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from subscriptions.models import Plan, Subscription
from .models import Video


User = get_user_model()


class VideoAccessTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('ali', 'ali@example.com', 'pass12345!')
        self.premium = Video.objects.create(
            title='Premium', file_url='https://example.com/p.mp4', required_tier=2
        )
        self.free = Video.objects.create(
            title='Free', file_url='https://example.com/f.mp4', required_tier=0
        )
        self.client.force_authenticate(self.user)

    def _subscribe(self, tier, days):
        plan = Plan.objects.create(name=f'T{tier}', tier=tier, price=100, duration_days=30)
        now = timezone.now()
        Subscription.objects.create(
            user=self.user, plan=plan,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=days),
            status=Subscription.Status.ACTIVE,
        )

    def test_free_video_is_open_to_everyone(self):
        res = self.client.get(f'/api/videos/{self.free.pk}/')
        self.assertEqual(res.status_code, 200)

    def test_premium_video_blocked_without_subscription(self):
        res = self.client.get(f'/api/videos/{self.premium.pk}/')
        self.assertEqual(res.status_code, 403)

    def test_premium_video_open_with_premium_subscription(self):
        self._subscribe(tier=2, days=10)
        res = self.client.get(f'/api/videos/{self.premium.pk}/')
        self.assertEqual(res.status_code, 200)

    def test_basic_subscription_cannot_open_premium(self):
        self._subscribe(tier=1, days=10)
        res = self.client.get(f'/api/videos/{self.premium.pk}/')
        self.assertEqual(res.status_code, 403)

    def test_expired_subscription_loses_access(self):
        self._subscribe(tier=2, days=-1)
        res = self.client.get(f'/api/videos/{self.premium.pk}/')
        self.assertEqual(res.status_code, 403)

    def test_watch_increments_views_and_saves_history(self):
        res = self.client.post(f'/api/videos/{self.free.pk}/watch/', {'progress_seconds': 42})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['views_count'], 1)
        hist = self.client.get('/api/history/')
        self.assertEqual(hist.data['results'][0]['progress_seconds'], 42)