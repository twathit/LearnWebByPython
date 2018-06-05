#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'Edward'
import re, time, json, logging, hashlib, asyncio, os
import markdown2
from aiohttp import web
from coroweb import get, post
from models import User, Comment, Blog, next_id
from apis import Page, APIError, APIValueError, APIResourceNotFoundError, APIPermissionError
from config import configs

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

def check_admin(request):
    if not request.__user__.admin:            
        if request.__user__ is None:
            raise APIPermissionError()
    else:
        return True

def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p

def user2cookie(user, max_age):
    expires = str(int(time.time()+max_age))
    s = '%s-%s-%s-%s' % (user.id, user.password, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

def text2html(text):
    lines = map(lambda s: '<p>%s<p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

@asyncio.coroutine
def cookie2user(cookie_str):
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = yield from User.find(uid)
        logging.info(user)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.password, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.password = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None
'''
@get('/')
async def index(request):
    summary='My first web site,take me quite a long time.Hope it will get better.'
    blogs=[
        Blog(id='1',name='Test Blog',summary=summary,created_at=time.time()-120),
        Blog(id='2', name='Some thing New', summary=summary, created_at=time.time() - 3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time() - 7200),
    ]
    return{
        '__template__':'blogs.html',
        'blogs':blogs
    }
'''
@get('/')
def index(*, page='1'):
    page_index = get_page_index(page)
    num = yield from Blog.findNumber('count(id)')
    page = Page(num, page_index)
    if num == 0:
        blogs = []
    else:
        blogs = yield from Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))
    for blog in blogs:
        if blog.tags:
            blog.tags = blog.tags.split(',')
        else:
            blog.tags = []
        blog.html_content = markdown2.markdown(blog.content)
    return {
            '__template__': 'blogs.html',
            'page': page,
            'blogs': blogs
        }

@get('/blogs/{tag}')
def get_blogs(*,tag, page='1'):
    page_index = get_page_index(page)
    num = yield from Blog.findNumber('count(id)')
    page = Page(num, page_index)
    if num == 0:
        blogs = []
    else:
        blogs = yield from Blog.findAll('find_in_set(?,tags)', [tag], orderBy='created_at desc', limit=(page.offset, page.limit))
    return {
            '__template__': 'tag_blogs.html',
            'page': page,
            'blogs': blogs
        }


@get('/blog/{id}')
def get_blog(id):
    blog = yield from Blog.find(id)
    blog.count+=1
    yield from blog.update()
    user_name = blog.user_name
    user = yield from User.findFirst('name=?',[user_name])
    comments = yield from Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    if blog.tags:
        blog.tags = blog.tags.split(',')
    else:
        blog.tags = []
    blog.html_content = markdown2.markdown(blog.content,extras=['fenced-code-blocks'])
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments,
        'user':user
    }

@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }

@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }

@post('/api/authenticate')
def authenticate(*, email, password):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not password:
        raise APIValueError('password', 'Invalid password')
    users = yield from User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email','Email not exist.')
    user = users[0]
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(password.encode('utf-8'))
    if user.password != sha1.hexdigest():
        raise APIValueError('password','Invalid password.')
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r

@get('/manage/')
def manage():
    return 'redirect:/manage/comments'

# @get('/manage/comments')
# def manage_comments(*, page='1'):
#     return {
#         '__template__': 'manage_comments.html',
#         'page_index': get_page_index(page)
#     }

@get('/manage/comments/{name}')
def manage_comments(*,name, page='1'):
    user = yield from User.findFirst('name=?',[name])
    return {
        '__template__': 'manage_comments.html',
        'page_index': get_page_index(page),
        'user':user
    }

@get('/manage/blogs/{name}')
def manage_blogs(*,name, page='1'):
    user = yield from User.findFirst('name=?',[name])
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page),
        'user':user
    }

@get('/manage/blog/create')
def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }

@get('/manage/blog/edit')
def manage_edit_blog(*, id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'action': '/api/blogs/%s' % id
    }
# @get('/manage/users')
# def manage_users(*, page='1'):
#     return {
#         '__template__': 'manage_users.html',
#         'page_index': get_page_index(page)
#     }

@get('/manage/users/{name}')
def manage_users(*,name, page='1'):
    user = yield from User.findFirst('name=?',[name])
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page),
        'user':user
    }

@get('/api/comments')
def api_comments(*, page='1'):
    page_index = get_page_index(page)
    num = yield from Comment.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = yield from Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)

@post('/api/blogs/{id}/comments')
def api_create_comment(id, request, *, content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('Please signin first.')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = yield from Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name, user_image=user.image, content=content.strip())
    yield from comment.save()
    return comment

@post('/api/comments/{id}/delete')
def api_delete_comments(id, request):
    check_admin(request)
    c = yield from Comment.find(id)
    if c is None:
        raise APIResourceNotFoundError('Comment')
    yield from c.remove()
    return dict(id=id)

@get('/api/users')
def api_get_users(*, page='1'):
    page_index = get_page_index(page)
    num = yield from User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = yield from User.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    for u in users:
        u.password='******'
    return dict(page=p, users=users)

_RE_EMAIL=re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1=re.compile(r'^[0-9a-f]{40}$')

@post('/api/users')
def api_register_user(*, email, name, password):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not password or not _RE_SHA1.match(password):
        raise APIValueError('password')
    users = yield from User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    uid = next_id()
    sha1_password = '%s:%s' % (uid, password)
    user = User(id=uid, name=name.strip(), email=email, password=hashlib.sha1(sha1_password.encode('utf-8')).hexdigest(), image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    yield from user.save()
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/api/blogs')
def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = yield from Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = yield from Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)

@get('/api/blogs/{id}')
def api_get_blog(*, id):
    blog = yield from Blog.find(id)
    if blog.tags:
        blog.tags = blog.tags.split(',')
    else:
        blog.tags = []
    return blog

@get('/api/userblogs')
def api_get_userblog(*,user_name, page='1'):
    page_index = get_page_index(page)
    num = yield from Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = yield from Blog.findAll('user_name=?',[user_name], orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)

@get('/api/usercomments')
def api_get_usercomment(*,user_name, page='1'):
    page_index = get_page_index(page)
    num = yield from Comment.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    comments = yield from Comment.findAll('user_name=?',[user_name], orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)

@post('/api/blogs')
def api_create_blog(request, *, name, tags, summary, content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    # if not summary or not summary.strip():
    #     raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty')
    tag_name = ','.join(tags)
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip(), tags = tag_name.strip())
    yield from blog.save()
    return blog

@post('/api/blogs/{id}')
def api_update_blog(id, request, *, name, summary, content, tags):
    check_admin(request)
    blog = yield from Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    # if not summary or not summary.strip():
    #     raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    tag_name = ','.join(tags)
    blog.tags = tag_name.strip()
    yield from blog.update()
    return blog

@post('/api/blogs/{id}/delete')
def api_delete_blog(request, *, id):
    check_admin(request)
    blog=yield from Blog.find(id)
    yield from blog.remove()
    return dict(id=id)

@post('/api/img')
def api_save_img(request,image):
    check_admin(request)
    filename = str(int time.time()+'.jpg')
    filepath = os.path.join('/static/images/img',filename)
    with open(filepath,'wb') as f:
        f.write(image)
    return filepath

