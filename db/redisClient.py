# -*- coding: utf-8 -*-
"""
-----------------------------------------------------
   File Name：     redisClient.py
   Description :   封装Redis相关操作
   Author :        JHao
   date：          2019/8/9
------------------------------------------------------
   Change Activity:
                   2019/08/09: 封装Redis相关操作
                   2020/06/23: 优化pop方法, 改用hscan命令
                   2021/05/26: 区别http/https代理
------------------------------------------------------
"""
__author__ = 'JHao'

from redis.exceptions import TimeoutError, ConnectionError, ResponseError
from redis.connection import BlockingConnectionPool
from handler.logHandler import LogHandler
from random import choice
from redis import Redis
import json


class RedisClient(object):
    """
    Redis client

    Redis中代理存放的结构为hash：
    key为ip:port, value为代理属性的字典;

    """

    def __init__(self, **kwargs):
        """
        init
        :param host: host
        :param port: port
        :param password: password
        :param db: db
        :return:
        """
        self.name = ""
        kwargs.pop("username")
        self.__conn = Redis(connection_pool=BlockingConnectionPool(decode_responses=True,
                                                                   timeout=5,
                                                                   socket_timeout=5,
                                                                   **kwargs))

    def get(self, proxy_type=None):
        """
        返回一个代理
        :param proxy_type: None=任意, 'https'=支持https的http代理,
                           'socks4'/'socks4a'/'socks5'=对应协议代理
        :return:
        """
        proxies = self.__conn.hvals(self.name)
        if proxy_type:
            proxies = self._filter_by_type(proxies, proxy_type)
        else:
            proxies = list(proxies)
        return choice(proxies) if proxies else None

    def put(self, proxy_obj):
        """
        将代理放入hash, 使用changeTable指定hash name
        :param proxy_obj: Proxy obj
        :return:
        """
        data = self.__conn.hset(self.name, proxy_obj.proxy, proxy_obj.to_json)
        return data

    def pop(self, proxy_type=None):
        """
        弹出一个代理
        :param proxy_type: 同get方法
        :return: dict {proxy: value}
        """
        proxy = self.get(proxy_type)
        if proxy:
            self.__conn.hdel(self.name, json.loads(proxy).get("proxy", ""))
        return proxy if proxy else None

    def delete(self, proxy_str):
        """
        移除指定代理, 使用changeTable指定hash name
        :param proxy_str: proxy str
        :return:
        """
        return self.__conn.hdel(self.name, proxy_str)

    def exists(self, proxy_str):
        """
        判断指定代理是否存在, 使用changeTable指定hash name
        :param proxy_str: proxy str
        :return:
        """
        return self.__conn.hexists(self.name, proxy_str)

    def update(self, proxy_obj):
        """
        更新 proxy 属性
        :param proxy_obj:
        :return:
        """
        return self.__conn.hset(self.name, proxy_obj.proxy, proxy_obj.to_json)

    def getAll(self, proxy_type=None):
        """
        字典形式返回所有代理, 使用changeTable指定hash name
        :param proxy_type: None=全部, 'https'/'socks4'/'socks4a'/'socks5'=按协议过滤
        :return:
        """
        items = self.__conn.hvals(self.name)
        if proxy_type:
            return self._filter_by_type(items, proxy_type)
        return list(items)

    def clear(self):
        """
        清空所有代理, 使用changeTable指定hash name
        :return:
        """
        return self.__conn.delete(self.name)

    def getCount(self):
        """
        返回代理数量
        :return:
        """
        proxies = self.getAll()
        protocol_dict = {}
        for item in proxies:
            d = json.loads(item)
            protocol = d.get("protocol", "http")
            protocol_dict[protocol] = protocol_dict.get(protocol, 0) + 1
        https_count = len([x for x in proxies if json.loads(x).get("https")])
        return {'total': len(proxies), 'https': https_count, 'protocol': protocol_dict}

    def _filter_by_type(self, items, proxy_type):
        """
        按代理类型过滤
        :param items: list of JSON strings
        :param proxy_type: 'https' 或 'socks4'/'socks4a'/'socks5'
        :return: filtered list
        """
        if proxy_type == "https":
            return list(filter(lambda x: json.loads(x).get("https"), items))
        else:
            return list(filter(lambda x: json.loads(x).get("protocol", "http") == proxy_type, items))

    def changeTable(self, name):
        """
        切换操作对象
        :param name:
        :return:
        """
        self.name = name

    def test(self):
        log = LogHandler('redis_client')
        try:
            self.getCount()
        except TimeoutError as e:
            log.error('redis connection time out: %s' % str(e), exc_info=True)
            return e
        except ConnectionError as e:
            log.error('redis connection error: %s' % str(e), exc_info=True)
            return e
        except ResponseError as e:
            log.error('redis connection error: %s' % str(e), exc_info=True)
            return e


