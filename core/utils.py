from .models import RecentActivity, UserCustom
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject

def get_logged_in_user(request):
    """
    Safely fetches the logged-in UserCustom instance based on session.
    Returns UserCustom instance or None.
    """
    user_id = request.session.get('user_id')
    if user_id:
        try:
            return UserCustom.objects.get(id=user_id)
        except UserCustom.DoesNotExist:
            return None
    return None

def log_activity(user, action, instance, message=None):
    """
    Logs user activity in RecentActivity table.
    :param user: UserCustom instance or None
    :param action: 'created', 'updated', 'deleted', etc.
    :param instance: model instance acted upon
    """

    # Ensure user_for_log is either a UserCustom instance or None
    if isinstance(user, SimpleLazyObject):
        user = user._wrapped

    if isinstance(user, UserCustom):
        user_for_log = user
    else:
        user_for_log = None

    if instance is None:
        model_name = "System"
        object_id = 0
        object_repr = message or ""
    else:
        model_name = instance.__class__.__name__
        object_id = instance.pk or 0
        object_repr = str(instance)

    if not object_repr and message:
        object_repr = message

    # Truncate long representations
    if len(object_repr) > 200:
        object_repr = object_repr[:197] + '...'

    # Deduplication prevention (skip duplicate logs within 5 min)
    window = timezone.now() - timedelta(minutes=5)
    if RecentActivity.objects.filter(
        user=user_for_log,
        action=action,
        model_name=model_name,
        object_id=object_id,
        timestamp__gte=window
    ).exists():
        return

    # Create the log entry
    RecentActivity.objects.create(
        user=user_for_log,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr
    )
