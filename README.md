### Django 做的一个小型论坛

***


#### 安装部署


依赖MySQL数据库,以及memcached

##安装方法：
1. 获取代码
2. 安装依赖
3. 导入数据库文件
4. 修改配置文件
5. 运行服务

```shell
shell> git clone https://github.com/eenot/eenot.git

shell> cd forum
shell> pip install -r requirements.txt

shell> mysql -u YOURUSERNAME -p

mysql> create database forum;
mysql> exit

shell> mysql -u YOURUSERNAME -p --database=forum < forum.sql
```

修改`xp/settings.py`

```python
# mysql数据库的配置在这里
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

# 修改memcached配置,如果没有memcahed 可以直接删除与cache相关的内容
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
EMAIL_HOST_USER= 'admin@eenot.com'
EMAIL_HOST_PASSWORD= '******'
DEFAULT_FROM_EMAIL = 'admin@eenot.com'
```

运行服务

```shell
python manage.py runserver
```

默认超级用户`admin@forum.com`,密码`123456`,后台`/manage/admin/`

生产环境下推荐使用gunicorn.



1. 实现了一个OAuth2.0授权服务;
2. 实现了topic的RESTful风格的api:
   * 获取topic列表 GET /api/topics
   * 创建topic POST /api/topics
   * 获取单个topic GET /api/topics/:id
   * 修改topic PUT /api/topics/:id
   * 获取回复列表 GET /api/topics/:id/replies
   * 创建回复 POST /api/topics/:id/replies

以上api POST PUT时需要用到授权`access_token`.
