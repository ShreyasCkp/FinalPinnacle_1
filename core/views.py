from django.shortcuts import render
from .models import RecentActivity
from master.models import UserCustom
from master.decorators import custom_login_required
from django.core.paginator import Paginator
@custom_login_required
def recent_activity_view(request):
    all_activities = RecentActivity.objects.order_by('-timestamp')

    paginator = Paginator(all_activities, 100)  # 100 activities per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    activities = page_obj.object_list  # Only current page

    # Efficiently extract user_ids from current page
    user_ids = [activity.user_id for activity in activities if activity.user_id]

    users = UserCustom.objects.filter(id__in=user_ids).values('id', 'username')
    user_dict = {user['id']: user['username'] for user in users}

    # Annotate each activity with username
    for activity in activities:
        activity.username = user_dict.get(activity.user_id, "Unknown")

    return render(request, 'core/recent_activity.html', {
        'page_obj': page_obj,
        'activities': activities,
    })

