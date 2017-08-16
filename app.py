# -*- coding: utf-8 -*-
__author__ = 'Edward'
import logging;logging.basicConfig(level=logging.INFO)
import asyncio,orm,json,time,os
from aiohttp import web
from coroweb import add_routes,add_static
from config import configs
from datetime import datetime
from jinja2 import Environment,FileSystemLoader
def init_jinja2(app,**kw):
    logging.info('init jinja2...')
    options=dict(
        autoescape=kw.get('autoescape',True),
        block_start_string=kw.get('block_start_string','{%'),
        block_end_string=kw.get('block_end_string','%}'),
        variable_start_string=kw.get('variable_start_string','{{'),
        variable_end_string=kw.get('variable_end_string','}}'),
        auto_reload=kw.get('auto_reload',True)
    )
    path=kw.get('path',None)
    if path is None:
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
    logging.info('set jinja2 template path:%s'%path)
    env=Environment(loader=FileSystemLoader(path),**options)
    filters=kw.get('filters',None)
    if filters is not None:
        for name,f in filters.items():
            env.filters[name]=f
    app['__templating__']=env
async def logger_factory(app,handler):
    async def logger(request):
        logging.info('Request:%s %S'%(request.method,request.path))
        return (await handler(request))
    return logger
async def data_factory(app,handler):
    async def parse_data(request):
        if request.method='POST':
            if request.content_type.startswith('application/json'):
                request.__data__=await request.json()
                logging.info('request jsaon: %s'%str(request.__data__))
            elif request.contnet_type.startswith('application/x-www-form-urlencoded'):
                request.__data__=await request.post()
                logging.info('request form:%s'%str(request.__data__))
        return (await handler(request))
    return parse_data
async def response_factory(app,handler):
    async def response(request):
        logging.info('Response handler...')
        r=await handler(request)
        if isinstance(r,web.StreamResponse):
            return r
        if isinstance(r,bytes):
            resp=web.Response(body=r)
        if isinstance(r,str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp=web.Response(body=r.encode('utf-8'))
            resp.content_type='text/html;charset=utf-8'
            return resp
        if isinstance(r,dict):
            template=r.get('__template__')
            if template is None:
                resp=web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type='application/json;charset=utf-8'
            else:
                resp=web.Response(body=app['__template__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type='text/html;charset=utf-8'
                return resp
        if isinstance(r,int) and r>=100 and r<=600:
            return web.Response(r)
        if isinstance(r,tuple) and len(r)==2:
            t,m=r
            if isinstance(t,int) and t>=100 and t<=600:
                return web.Response(t,str(m))
        resp=web.Response(body=str(r).encode('utf-8'))
        resp.content_type='text/plain;charset=utf-8'
        return resp
    return response
async def init(loop):
    await orm.create_pool(loop=loop,**configs.db)
    app=web.Application(loop=loop,middlewares=[logger_factory,auth_factory,response_factory])
    init_jinja2(app,filters=dict(datetime=datetime_filter))
    add_routes(app,'handlers')
    add_static(app)
    srv=await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv
loop=asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()