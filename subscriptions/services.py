from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import Payment, Subscription
from . import gateway


STAFF_TIER = 999


class SubscriptionError(Exception):
    """Logic error (message shown to user)"""


class PaymentFailed(SubscriptionError):
    pass


def get_current_subscription(user):
    """current sub that is valid or None"""
    return Subscription.objects.filter(
        user=user,
        status__in=[Subscription.Status.ACTIVE, Subscription.Status.CANCELED],
        end_date__gt=timezone.now(),
    ).select_related('plan').first()


def get_user_tier(user):
    if user.is_staff:
        return STAFF_TIER
    sub = get_current_subscription(user)
    return sub.plan.tier if sub else 0


def _pay(user, plan):
    success, ref_id = gateway.charge(user, plan.price)
    return Payment.objects.create(
        user=user,
        amount=plan.price,
        status=Payment.Status.SUCCESS if success else Payment.Status.FAILED,
        ref_id=ref_id,
    )


@transaction.atomic
def _extend(sub, payment):
    now = timezone.now()
    if sub.end_date > now:
        base = sub.end_date
    else:
        base = now
        sub.start_date = now
    sub.end_date = base + timedelta(days=sub.plan.duration_days)
    sub.status = Subscription.Status.ACTIVE
    sub.save()
    payment.subscription = sub
    payment.save(update_fields=['subscription'])
    return sub


def subscribe(user, plan):
    if get_current_subscription(user):
        raise SubscriptionError('You already have a valid subscription. Use renew instead.')

    payment = _pay(user, plan)
    if payment.status != Payment.Status.SUCCESS:
        raise PaymentFailed('Payment failed. No subscription was created.')

    with transaction.atomic():
        now = timezone.now()
        sub = Subscription.objects.create(
            user=user,
            plan=plan,
            start_date=now,
            end_date=now + timedelta(days=plan.duration_days),
            status=Subscription.Status.ACTIVE,
            auto_renew=True,
        )
        payment.subscription = sub
        payment.save(update_fields=['subscription'])
    return sub


def renew(user):
    sub = Subscription.objects.filter(user=user).select_related('plan').first()
    if sub is None:
        raise SubscriptionError('You have no subscription to renew. Subscribe first.')

    payment = _pay(user, sub.plan)
    if payment.status != Payment.Status.SUCCESS:
        raise PaymentFailed('Payment failed. Subscription was not renewed')

    sub.auto_renew = True
    return _extend(sub, payment)


def cancel(user):
    sub = get_current_subscription(user)
    if sub is None:
        raise SubscriptionError('You have no active subscription.')
    if sub.status == Subscription.Status.CANCELED:
        raise SubscriptionError('Your subscription is already canceled.')

    sub.status = Subscription.Status.CANCELED
    sub.auto_renew = False
    sub.save(update_fields=['status', 'auto_renew'])
    return sub


def process_due_subscriptions():
    now = timezone.now()
    renewed = expired = 0
    due = Subscription.objects.filter(
        end_date__lte=now,
        status__in=[Subscription.Status.ACTIVE, Subscription.Status.CANCELED],
    ).select_related('plan', 'user')

    for sub in due:
        if sub.status == Subscription.Status.ACTIVE and sub.auto_renew:
            payment = _pay(sub.user, sub.plan)
            if payment.status == Payment.Status.SUCCESS:
                _extend(sub, payment)
                renewed += 1
                continue
        sub.status = Subscription.Status.EXPIRED
        sub.save(update_fields=['status'])
        expired += 1
    return renewed, expired

