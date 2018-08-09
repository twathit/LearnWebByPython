#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'Edward'
import logging;logging.basicConfig(level=logging.INFO)
import asyncio, orm, json, time, os
from aiohttp import web
from coroweb import add_routes,add_static
from config import configs
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from handlers import cookie2user,COOKIE_NAME

def init_jinja2(app,**kw):
    logging.info('init jinja2...')
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload=kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path:%s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env

async def logger_factory(app,handler):
    async def logger(request):
        logging.info('Request:%s %s' % (request.method, request.path))
        return (await handler(request))
    return logger

async def auth_factory(app,handler):
    async def auth(request):
        logging.info('check user:%s %s' % (request.method, request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user = await cookie2user(cookie_str)
            if user:
                logging.info('set current user:%s' % user.email)
                request.__user__ = user
        if request.path.startswith('/manage/') and request.__user__ is None:         #or not request.__user__.admin):
            return web.HTTPFound('/signin')
        return (await handler(request))
    return auth

async def data_factory(app,handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.contnet_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form:%s' % str(request.__data__))
        return (await handler(request))
    return parse_data

'''
目前为止，aiohttp.web提供三个不同的响应类: StreamResponse, Response和FileResponse。
通常你要使用的是第二个也就是Response。StreamResponse用于流数据，Response会将HTTP主体保存在一个属性中，以正确的Content-Length头信息发送自己的内容。
为了设计考虑，Response的父类是StreamResponse。
StreamResponse拥有方法set_cookie(name, value, *, path='/', expires=None, domain=None, max_age=None, secure=None, httponly=None, version=None)
name (str) - cookie名称。
value (str) - cookie值（如果是其他类型的话会尝试转换为str类型）
expires - 过期时间（可选）。
domain (str) - cookie主域（可选）。
max_age (int) - 定义cookie的生命时长，以秒为单位。该参数为非负整数。在经过这些秒后，客户端会抛弃该cookie。如果设置为0则表示立即抛弃。
path (str) - 设置该cookie应用在哪个路径上（可选，默认是'/'）。
secure (bool) - 该属性（没有任何值）会让用户代理使用安全协议。用户代理（或许会在用户控制之下）需要决定安全等级，在适当的时候考虑使用“安全”cookie。是不是要使用“安全”要考虑从服务器到用户代理的这段历程，“安全”协议的目的是保证会话在安全情况下进行（可选）。
httponly (bool) - 如果要设置为HTTP only则为True（可选）。
version (int) - 一个十进制数，表示使用哪个版本的cookie管理（可选，默认为1）。

web.Response(*, body=None, status=200, reason=None, text=None, headers=None, content_type=None, charset=None)
body (bytes) - 响应主体。
status (int) - HTTP状态码，默认200。
headers (collections.abc.Mapping) - HTTP 头信息，会被添加到响应里。
text (str) - 响应主体。
content_type (str) - 响应的内容类型。如果有传入text参数的话则为text/plain，否则是application/octet-stream。
charset (str) - 响应的charset。如果有传入text参数则为utf-8，否则是None。
'''
async def response_factory(app, handler):
    async def response(request):
        logging.info('Response handler...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                r['__user__'] = request.__user__
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r,int) and r>=100 and r<=600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t>=100 and t<=600:
                return web.Response(t, str(m))
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response

def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)

def get_summary(text):
    return text[0:100]+'...' if len(text)>=100 else text

async def init(loop):
    await orm.create_pool(loop=loop, **configs.db)
    app = web.Application(loop=loop, middlewares=[logger_factory, auth_factory, response_factory])
    init_jinja2(app, filters=dict(datetime=datetime_filter, summary=get_summary))
    add_routes(app, 'handlers')
    add_static(app)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
#url handlers决定对于什么url返回什么内容, middleware会根据内容的类型决定具体返回的形式.