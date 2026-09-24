from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from . import services
from .models import Payment, Plan
from .serializers import PaymentSerializer, PlanSerializer, SubscribeSerializer, SubscriptionSerializer


class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class MySubscriptionView(APIView):
    def get(self, request):
        sub = services.get_current_subscription(request.user)
        if sub is None:
            return Response({'detail': 'No valid subscription.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SubscriptionSerializer(sub).data)


class SubscribeView(APIView):
    def post(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            sub = services.subscribe(request.user, serializer.validated_data['plan'])
        except services.PaymentFailed as e:
            return Response({'detail': str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except services.SubscriptionError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(sub).data, status=status.HTTP_201_CREATED)


class RenewView(APIView):
    def post(self, request):
        try:
            sub = services.renew(request.user)
        except services.PaymentFailed as e:
            return Response({'detail': str(e)}, status=HTTP_402_PAYMENT_REQUIRED)
        except services.SubscriptionError as e:
            return Response({'detail': str(e)}, status=HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(sub).data)


class CancelView(APIView):
    def post(self, request):
        try:
            sub = services.cancel(request.user)
        except services.SubscriptionError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(sub).data)


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

