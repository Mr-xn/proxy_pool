# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File Name：     ProxyApi.py
   Description :   WebApi
   Author :       JHao
   date：          2016/12/4
-------------------------------------------------
   Change Activity:
                   2016/12/04: WebApi
                   2019/08/14: 集成Gunicorn启动方式
                   2020/06/23: 新增pop接口
                   2022/07/21: 更新count接口
-------------------------------------------------
"""
__author__ = 'JHao'

import platform
from werkzeug.wrappers import Response
from flask import Flask, jsonify, request

from util.six import iteritems
from helper.proxy import Proxy
from handler.proxyHandler import ProxyHandler
from handler.configHandler import ConfigHandler

app = Flask(__name__)
conf = ConfigHandler()
proxy_handler = ProxyHandler()


class JsonResponse(Response):
    @classmethod
    def force_type(cls, response, environ=None):
        if isinstance(response, (dict, list)):
            response = jsonify(response)

        return super(JsonResponse, cls).force_type(response, environ)


app.response_class = JsonResponse

api_list = [
    {"url": "/get", "params": "type: 'https'|'socks4'|'socks4a'|'socks5'|''", "desc": "get a proxy"},
    {"url": "/get_raw", "params": "type: 'https'|'socks4'|'socks4a'|'socks5'|''", "desc": "get a proxy in raw format (e.g. http://x.x.x.x:8080)"},
    {"url": "/pop", "params": "type: 'https'|'socks4'|'socks4a'|'socks5'|''", "desc": "get and delete a proxy"},
    {"url": "/delete", "params": "proxy: 'e.g. 127.0.0.1:8080'", "desc": "delete an unable proxy"},
    {"url": "/all", "params": "type: 'https'|'socks4'|'socks4a'|'socks5'|''", "desc": "get all proxy from proxy pool"},
    {"url": "/count", "params": "", "desc": "return proxy count"}
    # 'refresh': 'refresh proxy pool',
]

VALID_PROXY_TYPES = {"https", "socks4", "socks4a", "socks5"}


def _get_proxy_type(request):
    """Parse and normalize the 'type' query parameter."""
    t = request.args.get("type", "").lower().strip()
    return t if t in VALID_PROXY_TYPES else None


@app.route('/')
def index():
    return {'url': api_list}


@app.route('/get/')
def get():
    proxy_type = _get_proxy_type(request)
    proxy = proxy_handler.get(proxy_type)
    return proxy.to_dict if proxy else {"code": 0, "src": "no proxy"}


@app.route('/get_raw/')
def getRaw():
    proxy_type = _get_proxy_type(request)
    proxy = proxy_handler.get(proxy_type)
    if proxy:
        scheme = proxy.protocol if proxy.protocol in ("socks4", "socks4a", "socks5") else (
            "https" if proxy.https else "http"
        )
        return Response("{}://{}".format(scheme, proxy.proxy), mimetype='text/plain')
    return Response("no proxy", mimetype='text/plain')


@app.route('/pop/')
def pop():
    proxy_type = _get_proxy_type(request)
    proxy = proxy_handler.pop(proxy_type)
    return proxy.to_dict if proxy else {"code": 0, "src": "no proxy"}


@app.route('/refresh/')
def refresh():
    # TODO refresh会有守护程序定时执行，由api直接调用性能较差，暂不使用
    return 'success'


@app.route('/all/')
def getAll():
    proxy_type = _get_proxy_type(request)
    proxies = proxy_handler.getAll(proxy_type)
    return jsonify([_.to_dict for _ in proxies])


@app.route('/delete/', methods=['GET'])
def delete():
    proxy = request.args.get('proxy')
    status = proxy_handler.delete(Proxy(proxy))
    return {"code": 0, "src": status}


@app.route('/count/')
def getCount():
    proxies = proxy_handler.getAll()
    protocol_dict = {}
    source_dict = {}
    https_count = 0
    for proxy in proxies:
        protocol_dict[proxy.protocol] = protocol_dict.get(proxy.protocol, 0) + 1
        if proxy.https:
            https_count += 1
        for source in proxy.source.split('/'):
            source_dict[source] = source_dict.get(source, 0) + 1
    return {"protocol": protocol_dict, "https": https_count, "source": source_dict, "count": len(proxies)}


def runFlask():
    if platform.system() == "Windows":
        app.run(host=conf.serverHost, port=conf.serverPort)
    else:
        import gunicorn.app.base

        class StandaloneApplication(gunicorn.app.base.BaseApplication):

            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super(StandaloneApplication, self).__init__()

            def load_config(self):
                _config = dict([(key, value) for key, value in iteritems(self.options)
                                if key in self.cfg.settings and value is not None])
                for key, value in iteritems(_config):
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        _options = {
            'bind': '%s:%s' % (conf.serverHost, conf.serverPort),
            'workers': 4,
            'accesslog': '-',  # log to stdout
            'access_log_format': '%(h)s %(l)s %(t)s "%(r)s" %(s)s "%(a)s"'
        }
        StandaloneApplication(app, _options).run()


if __name__ == '__main__':
    runFlask()
