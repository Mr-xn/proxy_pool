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
                   2024/01/01: 新增region模糊过滤支持
-------------------------------------------------
"""
__author__ = 'JHao'

from random import choice
from helper.proxy import Proxy
from db.dbClient import DbClient
from handler.configHandler import ConfigHandler


class ProxyHandler(object):
    """ Proxy CRUD operator"""

    def __init__(self):
        self.conf = ConfigHandler()
        self.db = DbClient(self.conf.dbConn)
        self.db.changeTable(self.conf.tableName)

    @staticmethod
    def _filter_by_region(proxies, region=None, exclude_region=None):
        """
        按地区关键词过滤代理列表（大小写不敏感，子串匹配）。

        Args:
            proxies: Proxy 对象列表
            region: 只保留 region 字段包含该关键词的代理（None 表示不限制）
            exclude_region: 排除 region 字段包含该关键词的代理（None 表示不排除）
        Returns:
            过滤后的 Proxy 对象列表
        """
        if region:
            kw = region.lower()
            proxies = [p for p in proxies if kw in p.region.lower()]
        if exclude_region:
            kw = exclude_region.lower()
            proxies = [p for p in proxies if kw not in p.region.lower()]
        return proxies

    def get(self, proxy_type=None, region=None, exclude_region=None):
        """
        return a random proxy
        Args:
            proxy_type: None=任意, 'https'=支持https的http代理,
                        'socks4'/'socks4a'/'socks5'=对应协议代理
            region: 只返回 region 字段包含该关键词的代理（大小写不敏感）
            exclude_region: 排除 region 字段包含该关键词的代理（大小写不敏感）
        Returns:
            Proxy object or None
        """
        if region or exclude_region:
            proxies = self.getAll(proxy_type, region=region, exclude_region=exclude_region)
            return choice(proxies) if proxies else None
        proxy = self.db.get(proxy_type)
        return Proxy.createFromJson(proxy) if proxy else None

    def pop(self, proxy_type=None, region=None, exclude_region=None):
        """
        return and delete a useful proxy
        :param proxy_type: 同get方法
        :param region: 同get方法
        :param exclude_region: 同get方法
        :return:
        """
        if region or exclude_region:
            proxies = self.getAll(proxy_type, region=region, exclude_region=exclude_region)
            if not proxies:
                return None
            proxy = choice(proxies)
            self.db.delete(proxy.proxy)
            return proxy
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

    def getAll(self, proxy_type=None, region=None, exclude_region=None):
        """
        get all proxy from pool as Proxy list
        :param proxy_type: None=全部, 'https'/'socks4'/'socks4a'/'socks5'=按协议过滤
        :param region: 只返回 region 字段包含该关键词的代理（大小写不敏感）
        :param exclude_region: 排除 region 字段包含该关键词的代理（大小写不敏感）
        :return:
        """
        proxies = [Proxy.createFromJson(_) for _ in self.db.getAll(proxy_type)]
        return self._filter_by_region(proxies, region=region, exclude_region=exclude_region)

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
