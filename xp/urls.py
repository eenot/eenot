# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib.auth.decorators import login_required
from django.contrib import admin
admin.autodiscover()
admin.site.login = login_required(admin.site.login) # 设置admin登录的页面，settings.LOGIN_URL

import forum.urls

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'xp.views.home', name='home'),
    # url(r'^xp/', include('xp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^', include(forum.urls)),
    url(r'^manage/admin/', include(admin.site.urls)),
)
