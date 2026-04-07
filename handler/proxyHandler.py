# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     ProxyHandler.py
   Description :
   Author :       JHao
   date：          2016/12/3
-------------------------------------------------
   Change Activity:
                   2016/12/03:
                   2020/05/26: 区分http和https
-------------------------------------------------
"""
__author__ = 'JHao'

from helper.proxy import Proxy
from db.dbClient import DbClient
from handler.configHandler import ConfigHandler


class ProxyHandler(object):
    """ Proxy CRUD operator"""

    def __init__(self):
        self.conf = ConfigHandler()
        self.db = DbClient(self.conf.dbConn)
        self.db.changeTable(self.conf.tableName)

    def get(self, proxy_type=None):
        """
        return a proxy
        Args:
            proxy_type: None=任意, 'https'=支持https的http代理,
                        'socks4'/'socks4a'/'socks5'=对应协议代理
        Returns:
        """
        proxy = self.db.get(proxy_type)
        return Proxy.createFromJson(proxy) if proxy else None

    def pop(self, proxy_type=None):
        """
        return and delete a useful proxy
        :param proxy_type: 同get方法
        :return:
        """
        proxy = self.db.pop(proxy_type)
        if proxy:
            return Proxy.createFromJson(proxy)
        return None

    def put(self, proxy):
        """
        put proxy into use proxy
        :return:
        """
        self.db.put(proxy)

    def delete(self, proxy):
        """
        delete useful proxy
        :param proxy:
        :return:
        """
        return self.db.delete(proxy.proxy)

    def getAll(self, proxy_type=None):
        """
        get all proxy from pool as Proxy list
        :param proxy_type: None=全部, 'https'/'socks4'/'socks4a'/'socks5'=按协议过滤
        :return:
        """
        proxies = self.db.getAll(proxy_type)
        return [Proxy.createFromJson(_) for _ in proxies]

    def exists(self, proxy):
        """
        check proxy exists
        :param proxy:
        :return:
        """
        return self.db.exists(proxy.proxy)

    def getCount(self):
        """
        return raw_proxy and use_proxy count
        :return:
        """
        total_use_proxy = self.db.getCount()
        return {'count': total_use_proxy}
