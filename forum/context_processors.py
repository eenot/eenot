# coding: utf-8

def custom_proc(request):
    return dict(
        navigation_bar = [
            ('/', 'topic', '社区'),
            ('/members/', 'members', '成员'),
            ('/static/pages/timeline/index.html', 'timeline', '大事记'),
            ('/static/pages/nav/index.html', 'nav', '导航'),
        ],
    )
