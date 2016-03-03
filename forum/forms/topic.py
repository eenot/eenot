# coding: utf-8

from django import forms

class ReplyForm(forms.Form):
    content = forms.CharField(error_messages={
        'required': u'请填写回复内容',})


class CreateForm(forms.Form):
    title = forms.CharField(min_length=3, max_length=56,
        error_messages={
            'required': u'请填写帖子标题',
            'min_length': u'帖子标题长度过短（3-56个字符）',
            'max_length': u'帖子标题长度过长（3-56个字符）',
        })
    content = forms.CharField(min_length=15,
        error_messages={
            'required': u'请填写帖子内容',
            'min_length': u'帖子内容长度过短（少于15个字符）',
        })
