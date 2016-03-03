from django.conf.urls import patterns, include, url
from forum.forms.user import LoginForm

from views import common, user, topic, notification
from forum.sitemap import TopicSitemap

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'xp.views.home', name='home'),
    # url(r'^xp/', include('xp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^$', common.method_splitter, {'GET': topic.get_index}),
    url(r'^t/(\d+)/$', common.method_splitter, {'GET': topic.get_view, 'POST': topic.post_view}),
    url(r'^t/create/(.*)/$', common.method_splitter, {'GET': topic.get_create, 'POST': topic.post_create}),
    url(r'^t/edit/(.*)/$', common.method_splitter, {'GET': topic.get_edit, 'POST': topic.post_edit}),
    url(r'^reply/edit/(.*)/$', common.method_splitter, {'GET': topic.get_reply_edit, 'POST': topic.post_reply_edit}),
    url(r'^node/(.*)/$', common.method_splitter, {'GET': topic.get_node_topics}),
    url(r'^u/(.*)/topics/$', common.method_splitter, {'GET': topic.get_user_topics}),
    url(r'^u/(.*)/replies/$', common.method_splitter, {'GET': topic.get_user_replies}),
    url(r'^u/(.*)/favorites/$', common.method_splitter, {'GET': topic.get_user_favorites}),
    url(r'^u/(.*)/$', common.method_splitter, {'GET': topic.get_profile}),
    url(r'^vote/$', common.method_splitter, {'GET': topic.get_vote}),
    url(r'^favorite/$', common.method_splitter, {'GET': topic.get_favorite}),
    url(r'^unfavorite/$', common.method_splitter, {'GET': topic.get_cancel_favorite}),
    url(r'^notifications/$', common.method_splitter, {'GET': notification.get_list}),
    url(r'^members/$', common.method_splitter, {'GET': topic.get_members}),
    url(r'^setting/$', common.method_splitter, {'GET': user.get_setting, 'POST': user.post_setting}),
    url(r'^setting/avatar/$', common.method_splitter, {'GET': user.get_setting_avatar, 'POST': user.post_setting_avatar}),
    url(r'^setting/password/$', common.method_splitter, {'GET': user.get_settingpwd, 'POST': user.post_settingpwd}),
    url(r'^forgot/$', common.method_splitter, {'GET': user.get_forgotpwd, 'POST': user.post_forgotpwd}),
    url(r'^login/$', common.method_splitter, {'GET': user.get_login, 'POST': user.post_login}),
    url(r'^logout/$', common.method_splitter, {'GET': user.get_logout}),
    url(r'^register/$', common.method_splitter, {'GET': user.get_register, 'POST': user.post_register}),

    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': {'topics': TopicSitemap}}),
)
