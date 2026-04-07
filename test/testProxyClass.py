# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     testProxyClass
   Description :
   Author :        JHao
   date：          2019/8/8
-------------------------------------------------
   Change Activity:
                   2019/8/8:
                   2024/01/01: 新增protocol字段测试
-------------------------------------------------
"""
__author__ = 'JHao'

import json
from helper.proxy import Proxy, PROXY_PROTOCOLS


def testProxyClass():
    proxy = Proxy("127.0.0.1:8080")

    print(proxy.to_json)

    proxy.add_source("test")

    proxy_str = json.dumps(proxy.to_dict, ensure_ascii=False)

    print(proxy_str)

    print(Proxy.createFromJson(proxy_str).to_dict)


def testProxyProtocol():
    """测试protocol字段"""
    # 默认协议为http
    proxy = Proxy("127.0.0.1:1080")
    assert proxy.protocol == "http", "default protocol should be http"

    # 测试各SOCKS协议
    for proto in PROXY_PROTOCOLS:
        p = Proxy("127.0.0.1:1080", protocol=proto)
        assert p.protocol == proto, "protocol should be {}".format(proto)

    # 非法协议回退到http
    p = Proxy("127.0.0.1:1080", protocol="invalid")
    assert p.protocol == "http", "invalid protocol should fall back to http"

    # 通过setter设置协议
    p = Proxy("127.0.0.1:1080")
    p.protocol = "socks5"
    assert p.protocol == "socks5"
    p.protocol = "bad"
    assert p.protocol == "http", "setter should reject invalid protocol"

    # to_dict 包含protocol字段
    p = Proxy("127.0.0.1:1080", protocol="socks4a")
    d = p.to_dict
    assert "protocol" in d
    assert d["protocol"] == "socks4a"

    # createFromJson 恢复protocol字段
    p2 = Proxy.createFromJson(p.to_json)
    assert p2.protocol == "socks4a"

    # 旧数据（无protocol字段）默认为http
    old_json = json.dumps({"proxy": "1.2.3.4:8080", "https": False, "fail_count": 0,
                           "region": "", "anonymous": "", "source": "",
                           "check_count": 0, "last_status": "", "last_time": ""})
    p3 = Proxy.createFromJson(old_json)
    assert p3.protocol == "http", "missing protocol field should default to http"

    print("testProxyProtocol ok!")


if __name__ == '__main__':
    testProxyClass()
    testProxyProtocol()
