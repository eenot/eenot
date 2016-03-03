# coding: utf-8

import json, math, hashlib
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.utils import timezone
from django.conf import settings
from forum.models import ForumUser, Topic, Favorite, Vote, Reply, Node, Notification, Plane
from forum.forms.topic import ReplyForm, CreateForm
from common import find_mentions


def get_index(request):
    user = request.user
    if user.is_authenticated():
        counter = {
            'topics': user.topic_author.all().count(),
            'replies': user.reply_author.all().count(),
            'favorites': user.fav_user.all().count()
        }
        notifications_count = user.notify_user.filter(status=0).count()

    status_counter = {
        'users': ForumUser.objects.all().count(),
        'nodes': Node.objects.all().count(),
        'topics': Topic.objects.all().count(),
        'replies': Reply.objects.all().count(),
    }

    try:
        current_page = int(request.GET.get('p', '1'))
    except ValueError:
        current_page = 1

    topics, topic_page = Topic.objects.get_all_topic(current_page=current_page)
    planes = Plane.objects.all().prefetch_related('node_set')
    hot_nodes = Node.objects.get_all_hot_nodes()
    active_page = 'topic'
    return render_to_response('topic/topics.html', locals(),
        context_instance=RequestContext(request))


def get_view(request, topic_id, errors=None):
    try:
        topic = Topic.objects.get_topic_by_topic_id(topic_id)
    except Topic.DoesNotExist:
        raise Http404
    user = request.user
    if user.is_authenticated():
        counter = {
            'topics': user.topic_author.all().count(),
            'replies': user.reply_author.all().count(),
            'favorites': user.fav_user.all().count()
        }
        notifications_count = user.notify_user.filter(status=0).count()
        topic_favorited = Favorite.objects.filter(involved_topic=topic, owner_user=user).exists()

    reply_num = 106
    reply_count = topic.reply_count
    reply_last_page = (reply_count // reply_num + (reply_count % reply_num and 1)) or 1
    try:
        current_page = int(request.GET.get('p', reply_last_page))
    except ValueError:
        current_page = reply_last_page

    replies, reply_page = Reply.objects.get_all_replies_by_topic_id(topic.id, current_page=current_page, num = reply_num)
    active_page = 'topic'
    floor = reply_num * (current_page - 1)

    topic.reply_count = reply_page.total
    topic.hits = (topic.hits or 0) + 1
    topic.save()
    return render_to_response('topic/view.html', locals(),
        context_instance=RequestContext(request))


@login_required
def post_view(request, topic_id):
    try:
        topic = Topic.objects.select_related('author').get(pk=topic_id)
    except Topic.DoesNotExist:
        raise Http404
    form = ReplyForm(request.POST)
    if not form.is_valid():
        return get_view(request, topic_id, errors=form.errors)

    user = request.user
    try:
        last_reply = topic.reply_set.all().order_by('-created')[0]
    except IndexError:
        last_reply = None
    if last_reply:
        last_replied_fingerprint = hashlib.sha1(str(topic.id) + str(last_reply.author_id) + last_reply.content).hexdigest()
        new_replied_fingerprint = hashlib.sha1(str(topic.id) + str(user.id) + form.cleaned_data.get('content')).hexdigest()
        if last_replied_fingerprint == new_replied_fingerprint:
            errors = {'duplicated_reply': [u'回复重复提交']}
            return get_view(request, topic.id, errors=errors)

    now = timezone.now()
    reply = Reply(
        topic = topic,
        author = user,
        content = form.cleaned_data.get('content'),
        created = now,
    )
    reply.save()
    Topic.objects.filter(pk=topic.id).update(last_replied_by=user, last_replied_time=now, last_touched=now)

    notifications = []
    if user.id != topic.author.id:
        notification = Notification(
            content = form.cleaned_data.get('content'),
            status = 0,
            involved_type = 1, # 0: mention, 1: reply
            involved_user = topic.author,
            involved_topic = topic,
            trigger_user = user,
            occurrence_time = now,
        )
        notifications.append(notification)

    mentions = find_mentions(form.cleaned_data.get('content'))
    if user.username in mentions:
        mentions.remove(user.username)
    if topic.author.username in mentions:
        mentions.remove(topic.author.username)
    if mentions:
        mention_users = ForumUser.objects.filter(username__in=mentions)
        if mention_users:
            for mention_user in mention_users:
                notification = Notification(
                    content = form.cleaned_data.get('content'),
                    status = 0,
                    involved_type = 0, # 0: mention, 1: reply
                    involved_user = mention_user,
                    involved_topic = topic,
                    trigger_user = user,
                    occurrence_time = now,
                )
                notifications.append(notification)
    if notifications:
        Notification.objects.bulk_create(notifications)

    if user.id != topic.author.id:
        topic_time_diff = timezone.now() - topic.created
        reputation = topic.author.reputation or 0
        reputation = reputation + 2 * math.log(user.reputation or 0 + topic_time_diff.days + 10, 10)
        ForumUser.objects.filter(pk=topic.author.id).update(reputation=reputation)

    return redirect('/t/%s/#reply%s' % (topic.id, topic.reply_count + 1))


@login_required
def get_create(request, slug=None, errors=None):
    node = get_object_or_404(Node, slug=slug)
    user = request.user
    counter = {
        'topics': user.topic_author.all().count(),
        'replies': user.reply_author.all().count(),
        'favorites': user.fav_user.all().count()
    }
    notifications_count = user.notify_user.filter(status=0).count()
    node_slug = node.slug
    active_page = 'topic'
    return render_to_response('topic/create.html', locals(),
        context_instance=RequestContext(request))


@login_required
def post_create(request, slug=None):
    node = get_object_or_404(Node, slug=slug)

    form = CreateForm(request.POST)
    if not form.is_valid():
        return get_create(request, slug=slug, errors=form.errors)

    user = request.user
    try:
        last_created = user.topic_author.all().order_by('-created')[0]
    except IndexError:
        last_created = None

    if last_created: # 如果用户最后一篇的标题内容与提交的相同
        last_created_fingerprint = hashlib.sha1(last_created.title + \
            last_created.content + str(last_created.node_id)).hexdigest()
        new_created_fingerprint = hashlib.sha1(form.cleaned_data.get('title') + \
            form.cleaned_data.get('content') + str(node.id)).hexdigest()

        if last_created_fingerprint == new_created_fingerprint:
            errors = {'duplicated_topic': [u'帖子重复提交']}
            return get_create(request, slug=slug, errors=errors)

    now = timezone.now()
    topic = Topic(
        title = form.cleaned_data.get('title'),
        content = form.cleaned_data.get('content'),
        created = now,
        node = node,
        author = user,
        reply_count = 0,
        last_touched = now,
    )
    topic.save()

    reputation = user.reputation or 0
    reputation = reputation - 5 # 每次发布话题扣除用户威望5点
    reputation = 0 if reputation < 0 else reputation
    ForumUser.objects.filter(pk=user.id).update(reputation=reputation)

    return redirect('/')


@login_required
def get_edit(request, topic_id, errors=None):
    topic = get_object_or_404(Topic, pk=topic_id)

    user = request.user
    counter = {
        'topics': user.topic_author.all().count(),
        'replies': user.reply_author.all().count(),
        'favorites': user.fav_user.all().count()
    }
    notifications_count = user.notify_user.filter(status=0).count()

    active_page = 'topic'
    return render_to_response('topic/edit.html', locals(),
        context_instance=RequestContext(request))


@login_required
def post_edit(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)

    form = CreateForm(request.POST)
    if not form.is_valid():
        return get_edit(request, topic_id, errors=form.errors)

    user = request.user
    if topic.author_id != user.id:
        errors = {'invalid_permission': [u'没有权限修改该主题']}
        return get_edit(request, topic_id, errors=errors)

    now = timezone.now()
    Topic.objects.filter(pk=topic.id).update(updated=now, last_touched=now, **form.cleaned_data)

    reputation = user.reputation or 0
    reputation = reputation - 2 # 每次修改回复扣除用户威望2点
    reputation = 0 if reputation < 0 else reputation
    ForumUser.objects.filter(pk=user.id).update(reputation=reputation)

    return redirect('/t/%s/' % topic.id)


@login_required
def get_reply_edit(request, reply_id, errors=None):
    reply = get_object_or_404(Reply, pk=reply_id)
    user = request.user
    counter = {
        'topics': user.topic_author.all().count(),
        'replies': user.reply_author.all().count(),
        'favorites': user.fav_user.all().count()
    }
    notifications_count = user.notify_user.filter(status=0).count()
    active_page = 'topic'
    return render_to_response('topic/reply_edit.html', locals(),
        context_instance=RequestContext(request))


@login_required
def post_reply_edit(request, reply_id):
    reply = get_object_or_404(Reply, pk=reply_id)

    form = ReplyForm(request.POST)
    if not form.is_valid():
        return get_reply_edit(request, reply_id, errors=form.errors)

    user = request.user
    if reply.author_id != user.id:
        errors = {'invalid_permission': [u'没有权限修改该回复']}
        return get_reply_edit(request, reply_id, errors=errors)

    Reply.objects.filter(pk=reply.id).update(updated=timezone.now(), **form.cleaned_data)

    reputation = user.reputation or 0
    reputation = reputation - 2 # 每次修改回复扣除用户威望2点
    reputation = 0 if reputation < 0 else reputation
    ForumUser.objects.filter(pk=user.id).update(reputation=reputation)

    return redirect('/t/%s/' % reply.topic_id)


def get_node_topics(request, slug):
    node = get_object_or_404(Node, slug=slug)

    user = request.user
    if user.is_authenticated():
        counter = {
            'topics': user.topic_author.all().count(),
            'replies': user.reply_author.all().count(),
            'favorites': user.fav_user.all().count()
        }
        notifications_count = user.notify_user.filter(status=0).count()

    try:
        current_page = int(request.GET.get('p', '1'))
    except ValueError:
        current_page = 1

    topics, topic_page = Topic.objects.get_all_topics_by_node_slug(node_slug=slug, current_page=current_page)
    active_page = 'topic'
    return render_to_response('topic/node_topics.html', locals(),
        context_instance=RequestContext(request))


def get_user_topics(request, uid):
    try:
        if uid.isdigit():
            user_info = ForumUser.objects.get(pk=uid)
        else:
            user_info = ForumUser.objects.get(username=uid)
    except ForumUser.DoesNotExist:
        raise Http404

    try:
        current_page = int(request.GET.get('p', '1'))
    except ValueError:
        current_page = 1

    counter = {
        'topics': user_info.topic_author.all().count(),
        'replies': user_info.reply_author.all().count(),
        'favorites': user_info.fav_user.all().count()
    }

    user = request.user
    if user.is_authenticated():
        notifications_count = user.notify_user.filter(status=0).count()

    topics, topic_page = Topic.objects.get_user_all_topics(user_info.id, current_page=current_page)
    active_page = 'topic'
    return render_to_response('topic/user_topics.html', locals(),
        context_instance=RequestContext(request))


def get_user_replies(request, uid):
    try:
        if uid.isdigit():
            user_info = ForumUser.objects.get(pk=uid)
        else:
            user_info = ForumUser.objects.get(username=uid)
    except ForumUser.DoesNotExist:
        raise Http404

    try:
        current_page = int(request.GET.get('p', '1'))
    except ValueError:
        current_page = 1

    counter = {
        'topics': user_info.topic_author.all().count(),
        'replies': user_info.reply_author.all().count(),
        'favorites': user_info.fav_user.all().count()
    }

    user = request.user
    if user.is_authenticated():
        notifications_count = user.notify_user.filter(status=0).count()

    replies, reply_page = Reply.objects.get_user_all_replies(user_info.id, current_page=current_page)
    active_page = 'topic'
    return render_to_response('topic/user_replies.html', locals(),
        context_instance=RequestContext(request))


def get_user_favorites(request, uid):
    try:
        if uid.isdigit():
            user_info = ForumUser.objects.get(pk=uid)
        else:
            user_info = ForumUser.objects.get(username=uid)
    except ForumUser.DoesNotExist:
        raise Http404

    try:
        current_page = int(request.GET.get('p', '1'))
    except ValueError:
        current_page = 1

    counter = {
        'topics': user_info.topic_author.all().count(),
        'replies': user_info.reply_author.all().count(),
        'favorites': user_info.fav_user.all().count()
    }

    user = request.user
    if user.is_authenticated():
        notifications_count = user.notify_user.filter(status=0).count()

    favorites, favorite_page = Favorite.objects.get_user_all_favorites(user_info.id, current_page=current_page)
    active_page = 'topic'
    return render_to_response('topic/user_favorites.html', locals(),
        context_instance=RequestContext(request))


def get_profile(request, uid):
    try:
        if uid.isdigit():
            user_info = ForumUser.objects.get(pk=uid)
        else:
            user_info = ForumUser.objects.get(username=uid)
    except ForumUser.DoesNotExist:
        raise Http404

    try:
        current_page = int(request.GET.get('p', '1'))
    except ValueError:
        current_page = 1

    counter = {
        'topics': user_info.topic_author.all().count(),
        'replies': user_info.reply_author.all().count(),
        'favorites': user_info.fav_user.all().count()
    }

    user = request.user
    if user.is_authenticated():
        notifications_count = user.notify_user.filter(status=0).count()

    topics, topic_page = Topic.objects.get_user_all_topics(user_info.id, current_page=current_page)
    replies, reply_page = Reply.objects.get_user_all_replies(user_info.id, current_page=current_page)
    active_page = '_blank'
    return render_to_response('topic/profile.html', locals(),
        context_instance=RequestContext(request))


def get_vote(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponse(json.dumps({
            'success': 0,
            'message': 'user_not_login'
        }), content_type='application/json')

    try:
        topic_id = int(request.GET.get('topic_id'))
    except (TypeError, ValueError):
        topic_id = None
    topic = None
    if topic_id:
        try:
            topic = Topic.objects.select_related('author').get(pk=topic_id)
        except Topic.DoesNotExist:
            pass

    if not (topic_id and topic):
        return HttpResponse(json.dumps({
            'success': 0,
            'message': 'topic_not_exist'
        }), content_type='application/json')

    if user.id == topic.author.id:
        return HttpResponse(json.dumps({
            'success': 0,
            'message': 'can_not_vote_your_topic'
        }), content_type='application/json')

    if Vote.objects.filter(trigger_user=user, involved_topic=topic).exists():
        return HttpResponse(json.dumps({
            'success': 0,
            'message': 'already_voted'
        }), content_type='application/json')

    vote = Vote(trigger_user=user, involved_type=0, involved_topic=topic, \
        involved_user=topic.author, status=0, occurrence_time=timezone.now())
    vote.save()

    # 更新话题作者声誉
    topic_time_diff = timezone.now() - topic.created
    reputation = topic.author.reputation or 0
    reputation = reputation + 2 * math.log((user.reputation or 0) + topic_time_diff.days + 10, 10)
    ForumUser.objects.filter(pk=topic.author.id).update(reputation=reputation)

    return HttpResponse(json.dumps({
        'success': 1,
        'message': 'thanks_for_your_vote'
    }), content_type='application/json')


def get_favorite(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponse(json.dumps({
            'success': 0,
            'message': 'user_not_login'
        }), content_type='application/json')

    try:
        topic_id = int(request.GET.get('topic_id'))
    except (TypeError, ValueError):
        topic_id = None
    topic = None
    if topic_id:
        try:
            topic = Topic.objects.select_related('author').get(pk=topic_id)
        except Topic.DoesNotExist:
            pass

    if not (topic_id and topic):
        return HttpResponse(json.dumps({
            'success': 0,
            'message': 'topic_not_exist'
        }), content_type='application/json')

    if user.id == topic.author.id:
        return HttpResponse(json.dumps({
            'success': 0,
            'message': 'can_not_favorite_your_topic'
        }), content_type='application/json')

    if Favorite.objects.filter(owner_user=user, involved_topic=topic).exists():
        return HttpResponse(json.dumps({
            'success': 0,
            'message': 'already_favorited'
        }), content_type='application/json')

    favorite = Favorite(owner_user=user, involved_type=0, involved_topic=topic, created=timezone.now())
    favorite.save()

    # 更新话题作者声誉
    topic_time_diff = timezone.now() - topic.created
    reputation = topic.author.reputation or 0
    reputation = reputation + 2 * math.log((user.reputation or 0) + topic_time_diff.days + 10, 10)
    ForumUser.objects.filter(pk=topic.author.id).update(reputation=reputation)

    return HttpResponse(json.dumps({
        'success': 1,
        'message': 'cancel_favorite_success'
    }), content_type='application/json')


def get_cancel_favorite(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponse(json.dumps({
            'success': 0,
            'message': 'user_not_login'
        }), content_type='application/json')

    try:
        topic_id = int(request.GET.get('topic_id'))
    except (TypeError, ValueError):
        topic_id = None
    topic = None
    if topic_id:
        try:
            topic = Topic.objects.select_related('author').get(pk=topic_id)
        except Topic.DoesNotExist:
            pass

    if not (topic_id and topic):
        return HttpResponse(json.dumps({
            'success': 0,
            'message': 'topic_not_exist'
        }), content_type='application/json')

    try:
        favorite = Favorite.objects.get(owner_user=user, involved_topic=topic)
    except Favorite.DoesNotExist:
        favorite = None

    if not favorite:
        return HttpResponse(json.dumps({
            'success': 0,
            'message': 'not_been_favorited'
        }), content_type='application/json')

    favorite.delete()

    # 更新话题作者声誉
    topic_time_diff = timezone.now() - topic.created
    reputation = topic.author.reputation or 0
    reputation = reputation - math.log(user.reputation or 0 + topic_time_diff.days + 10, 15)
    ForumUser.objects.filter(pk=topic.author.id).update(reputation=reputation)

    return HttpResponse(json.dumps({
        'success': 1,
        'message': 'cancel_favorite_success'
    }), content_type='application/json')


def get_members(request):
    user = request.user
    if user.is_authenticated():
        counter = {
            'topics': user.topic_author.all().count(),
            'replies': user.reply_author.all().count(),
            'favorites': user.fav_user.all().count()
        }
        notifications_count = user.notify_user.filter(status=0).count()

    members = ForumUser.objects.all().order_by('-id')[:49]
    active_members = ForumUser.objects.all().order_by('-last_login')[:49]
    active_page = 'members'
    return render_to_response('topic/members.html', locals(),
        context_instance=RequestContext(request))
