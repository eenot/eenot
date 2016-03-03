# coding: utf-8

'''
Django模板引擎的自定义过滤器，需要在模板中引用
{% load forum_extras %}
'''


import json, re, random
from datetime import date, datetime
from django import template
from django.utils import timezone
from markdown import markdown


register = template.Library()


@register.filter(name='dump_errors')
def dump_errors(errors): # 显示错误信息
    t = template.Template('''
        {% if errors %}
        <ul class="errors alert alert-error">
            {% for v in errors.itervalues %}
                <li>{{ v | join:'，' }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        ''')
    c = template.Context(dict(errors = errors))

    return t.render(c)


@register.simple_tag
def build_uri(uri, param, value): # 给uri添加参数或者修改参数的值
    regx = re.compile('[\?&](%s=[^\?&]*)' % param)
    find = regx.search(uri)
    split = '&' if re.search(r'\?', uri) else '?'
    if not find: return '%s%s%s=%s' % (uri, split, param, value)
    return re.sub(find.group(1), '%s=%s' % (param, value), uri)


@register.simple_tag
def pagination(page, uri, list_rows = 10): # 显示分页
    def gen_page_list(current_page = 1, total_page = 1, list_rows = 10):
        if total_page <= list_rows:
            return range(1, total_page + 1)
        elif current_page <= (list_rows // 2):
            return range(1, list_rows + 1)
        elif current_page >= (total_page - list_rows // 2):
            return range(total_page - list_rows + 1, total_page + 1)
        else:
            return range(current_page - list_rows // 2, current_page - list_rows // 2 + list_rows)

    t = template.Template('''
        {% load forum_extras %} {# 如果要使用自定义tag filter这里也需要加载 #}
        {% if page and page.pages > 1 %}
            <ul>
                <li {% ifequal page.index page.prev %}class="disabled"{% endifequal %}><a href="{% build_uri uri 'p' page.prev %}">«</a></li>
                {% for p in gen_page_list %}
                    <li {% ifequal page.index p %}class="active"{% endifequal %}>
                        {% ifnotequal page.index p %}
                            <a href="{% build_uri uri 'p' p %}">{{ p }}</a>
                        {% else %}
                            <a href="javascript:;">{{ p }}</a>
                        {% endifnotequal %}
                    </li>
                {% endfor %}
                <li {% ifequal page.index page.next %}class="disabled"{% endifequal %}><a href="{% build_uri uri 'p' page.next %}">»</a></li>
            </ul>
        {% endif %}
        ''')
    c = template.Context(dict(page = page, uri = uri, gen_page_list = gen_page_list(page.index, page.pages, list_rows)))

    return t.render(c)


@register.filter(name='pretty_date')
def pretty_date(time = None): # 输出时间，格式化的时间
    '''
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    '''
    if time == None:
        return time

    now = timezone.now()
    if isinstance(time, basestring):
        time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    elif isinstance(time, int):
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return '刚刚'
        if second_diff < 60:
            return str(second_diff) + ' 秒前'
        if second_diff < 120:
            return  '1 分钟前'
        if second_diff < 3600:
            return str(second_diff / 60) + ' 分钟前'
        if second_diff < 7200:
            return '1 小时前'
        if second_diff < 86400:
            return str(second_diff / 3600) + ' 小时前'
    if day_diff == 1:
        return '昨天'
    if day_diff < 7:
        return str(day_diff) + ' 天前'
    if day_diff < 31:
        return str(day_diff / 7) + ' 周前'
    if day_diff < 365:
        return str(day_diff / 30) + ' 月前'
    return str(day_diff / 365) + ' 天前'


@register.filter(name='content_process')
def content_process(content): #内容处理，把gist，微博图片什么的替换为引用框架什么的
    # render content included gist
    content = re.sub(r'http(s)?:\/\/gist.github.com\/(\d+)(.js)?', r'<script src="http://gist.github.com/\2.js"></script>', content)
    # render sinaimg pictures
    content = re.sub(r'(http:\/\/\w+.sinaimg.cn\/.*?\.(jpg|gif|png))', r'<img src="\1" />', content)
    # render @ mention links
    content = re.sub(r'@(\w+)(\s|)', r'<a href="/u/\1/">@\1</a> ', content)
    # render youku videos
    content = re.sub(r'http://v.youku.com/v_show/id_(\w+).html', r'<iframe height=498 width=510 src="http://player.youku.com/embed/\1" frameborder=0 allowfullscreen style="width:100%;max-width:510px;"></iframe>', content)
    return content


@register.filter(name='markdown')
def markdown_up(content): # 转为markdown
    if not content:
        return ''
    return markdown(content, extensions = ['codehilite', 'fenced_code', 'mathjax'], safe_mode = 'escape')


@register.filter(name='email_mosaic')
def email_mosaic(email): # 隐藏email
    if not email:
        return ''

    email_name = re.findall(r'^([^@]+)@', email)[0]

    if len(email_name) < 5:
        email_name = email_name + '***'
        email = re.sub(r'^([^@]+)@', '%s@' % email_name, email)
    else:
        email = re.sub(r'[^@]{3}@', '***@', email)

    return email


@register.simple_tag
def gen_random(): # 生成随机数用语静态文件，避免静态文件被浏览器缓存
    return random.random()
