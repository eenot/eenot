# coding: utf-8


from django.contrib.sitemaps import Sitemap
from forum.models import Topic


class TopicSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return Topic.objects.all().order_by('-created', '-id')

    def lastmod(self, obj):
        return obj.created

    def location(self, obj):
        return '/t/%s/' % obj.id
