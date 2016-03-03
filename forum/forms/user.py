# coding: utf-8

from django import forms
from django.contrib.auth import authenticate
from django.conf import settings
from forum.models import ForumUser


error_messages = {
    'username': {
        'required': u'必须填写用户名',
        'min_length': u'用户名长度过短（3-12个字符）',
        'max_length': u'用户名长度过长（3-12个字符）',
        'invalid': u'用户名格式错误（英文字母开头，数字，下划线构成）'
    },
    'email': {
        'required': u'必须填写E-mail',
        'min_length': u'Email长度有误',
        'max_length': u'Email长度有误',
        'invalid': u'Email地址无效'
    },
    'password': {
        'required': u'必须填写密码',
        'min_length': u'密码长度过短（6-64个字符）',
        'max_length': u'密码长度过长（6-64个字符）'
    },
}


class SettingPasswordForm(forms.Form):
    password_old = forms.CharField(min_length=6, max_length=64,
        error_messages=error_messages.get('password'))
    password = forms.CharField(min_length=6, max_length=64,
        error_messages=error_messages.get('password'))
    password_confirm = forms.CharField(required=False)

    def __init__(self, request):
        self.user = request.user
        super(SettingPasswordForm, self).__init__(request.POST)

    def clean(self):
        password_old = self.cleaned_data.get('password_old')
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if not (password_old and self.user.check_password(password_old)):
            raise forms.ValidationError(u'当前输入旧密码有误')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(u'两次输入新密码不一致')
        return self.cleaned_data


class ForgotPasswordForm(forms.Form):
    username = forms.RegexField(min_length=3, max_length=12,
        regex=r'^[a-zA-Z][a-zA-Z0-9_]*$',
        error_messages=error_messages.get('username'))
    email = forms.EmailField(min_length=4, max_length=64,
        error_messages=error_messages.get('email'))

    def __init__(self, *args, **kwargs):
        self.user_cache = None
        super(ForgotPasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')

        if username and email:
            try:
                self.user_cache = ForumUser.objects.get(username=username, email=email)
            except ForumUser.DoesNotExist:
                raise forms.ValidationError(u'所填用户名和邮箱有误')
        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class LoginForm(forms.Form):
    email = forms.EmailField(min_length=4, max_length=64,
        error_messages=error_messages.get('email'))
    password = forms.CharField(min_length=6, max_length=64,
        error_messages=error_messages.get('password'))

    def __init__(self, *args, **kwargs):
        self.user_cache = None
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(username=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(u'邮箱或者密码不正确')
            elif not self.user_cache.is_active:
                raise forms.ValidationError(u'用户已被锁定，请联系管理员解锁')
        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class RegisterForm(forms.ModelForm):
    username = forms.RegexField(min_length=3, max_length=12,
        regex=r'^[a-zA-Z][a-zA-Z0-9_]*$',
        error_messages=error_messages.get('username'))
    email = forms.EmailField(min_length=4, max_length=64,
        error_messages=error_messages.get('email'))
    password = forms.CharField(min_length=6, max_length=64,
        error_messages=error_messages.get('password'))
    password_confirm = forms.CharField(required=False)

    class Meta:
        model = ForumUser
        fields = ('username', 'email')

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            ForumUser.objects.get(username=username)
            raise forms.ValidationError(u'所填用户名已经被注册过')
        except ForumUser.DoesNotExist:
            if username in settings.RESERVED:
                raise forms.ValidationError(u'用户名被保留不可用')
            return username

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            ForumUser.objects.get(email=email)
            raise forms.ValidationError(u'所填邮箱已经被注册过')
        except ForumUser.DoesNotExist:
            return email

    def clean_password_confirm(self):
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password_confirm')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(u'两次输入密码不一致')
        return password2

    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class SettingForm(forms.Form):
    username = forms.CharField() # readonly
    email = forms.EmailField() # readonly
    nickname = forms.CharField(min_length=3, max_length=12, required=False,
        error_messages={
            'min_length': u'昵称长度过短（3-12个字符）',
            'max_length': u'昵称长度过长（3-12个字符）',
        })
    signature = forms.CharField(required=False)
    location = forms.CharField(required=False)
    website = forms.URLField(required=False,
        error_messages={
            'invalid': u'请填写合法的URL地址（如：http://f2e.im）',
        })
    company = forms.CharField(required=False)
    github = forms.CharField(required=False)
    twitter = forms.CharField(required=False)
    douban = forms.CharField(required=False)
    self_intro = forms.CharField(required=False)
