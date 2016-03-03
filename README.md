### Django forum

***

demo: <http://djangoforum.coding.io/>

Django forum是使用Django实现的轻型现代论坛程序,是fork自[F2E.im](https://github.com/PaulGuo/F2E.im)的Django版本.  
相对于原版的主要区别在于使用Django admin实现了一个简单的后台管理.

Django forum有3个分支,master分支用于主机上部署,SAE分支是适配Sina App Engine的版本,api分支是一个试验性质的分支,详情见更新

#### 安装部署

主机版:

依赖MySQL数据库,以及memcached

1. 获取代码
2. 安装依赖
3. 导入数据库文件
4. 修改配置文件
5. 运行服务

```shell
shell> git clone git@github.com:zhu327/forum.git

shell> cd forum
shell> pip install -r requirements.txt

shell> mysql -u YOURUSERNAME -p

mysql> create database forum;
mysql> exit

shell> mysql -u YOURUSERNAME -p --database=forum < forum.sql
```

修改`xp/settings.py`

```python
# 修改数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'forum',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '3306',                      # Set to empty string for default.
    }
}

# 修改memcached配置,如果没有memcahed请删除这些与cache相关的内容
CACHES = { # memcached缓存设置
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache' # 使用memcached存储session

# 配置邮件发送
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 25
EMAIL_HOST_USER= '*********'
EMAIL_HOST_PASSWORD= '******'
DEFAULT_FROM_EMAIL = '*********@qq.com'
```

运行服务

```shell
python manage.py runserver
```

默认超级用户`admin@forum.com`,密码`123456`,后台`/manage/admin/`

生产环境下推荐使用gunicorn.

SAE版

SAE版本依赖已打包到site-packages.zip,头像存储使用七牛,所以还需要申请七牛云.

1. SAE上创建python应用,激活MySQL,memcached,创建应用版本
2. 获取代码
3. SAE MySQL后台导入forum.sql文件
4. 修改配置文件
5. 上传代码
6. 登录后台设置

```shell
shell> git clone -b sae git@github.com:zhu327/forum.git

shell> cd forum
```

登录SAE进入MySQL在线管理导入forum.sql

修改`xp/settings.py`

```python
# 邮件发送设置
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 25
EMAIL_HOST_USER= '*********'
EMAIL_HOST_PASSWORD= '******'
DEFAULT_FROM_EMAIL = '*********@qq.com'

# 七牛云存储设置
QINIU_ACCESS_KEY = '******'
QINIU_SECRET_KEY = '******'
QINIU_BUCKET_NAME = '******'
QINIU_BUCKET_DOMAIN = '******'
```

修改`config.yaml`

```yaml
name: way2go // 这里改为你自己的SAE应用名
version: 1
```

SVN上传即可.

#### 更新

SAE 版本新增功能,可使用`SAE kvdb`做缓存,缓存后端使用`xp.cache.SaekvdbCache`,减少云豆消耗.  
SAE激活kvdb并关闭`memcached`功能,修改`xp/settings.py`,`SAE kvdb`会比`memcached`慢一点,但是会便宜很多

```python
CACHES = { # memcached缓存设置
    'default': {
        # 'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache', # SAE使用pylibmc
        'BACKEND': 'xp.cache.SaekvdbCache', # 可选用SAE kvdb做缓存，消耗云豆更少
        'LOCATION': '127.0.0.1:11211',
    }
}
```

增加api分支,试验性质只为学习RESTful api实现.

1. 实现了一个OAuth2.0授权服务;
2. 实现了topic的RESTful风格的api:
   * 获取topic列表 GET /api/topics
   * 创建topic POST /api/topics
   * 获取单个topic GET /api/topics/:id
   * 修改topic PUT /api/topics/:id
   * 获取回复列表 GET /api/topics/:id/replies
   * 创建回复 POST /api/topics/:id/replies

以上api POST PUT时需要用到授权`access_token`.
