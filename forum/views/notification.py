# coding: utf-8

from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from forum.models import Notification


@login_required
def get_list(request):
    current_page = int(request.GET.get('p', '1'))
    user = request.user
    counter = {
        'topics': user.topic_author.all().count(),
        'replies': user.reply_author.all().count(),
        'favorites': user.fav_user.all().count()
    }

    notifications_count = user.notify_user.filter(status=0).count()
    notifications, page = Notification.objects.get_user_all_notifications(user.id, current_page=current_page)
    active_page = 'topic'

    user.notify_user.filter(status=0).update(status=1) # 未读消息设置为已读

    return render_to_response('notification/notifications.html', locals(),
        context_instance=RequestContext(request))
