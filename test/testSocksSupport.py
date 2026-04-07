# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     testSocksSupport
   Description :   SOCKS4/SOCKS4a/SOCKS5 协议支持单元测试
   Author :        JHao
   date：          2024/1/1
-------------------------------------------------
   Change Activity:
                   2024/01/01: 新增SOCKS协议支持测试
-------------------------------------------------
"""
__author__ = 'JHao'

import json
from unittest.mock import patch, MagicMock
from helper.proxy import Proxy, PROXY_PROTOCOLS
from helper.validator import ProxyValidator, formatValidator


# ---------------------------------------------------------------------------
# helper: build a minimal JSON string as stored in Redis
# ---------------------------------------------------------------------------

def _make_json(proxy="1.2.3.4:1080", protocol="http", https=False):
    return json.dumps({
        "proxy": proxy,
        "https": https,
        "protocol": protocol,
        "fail_count": 0,
        "region": "",
        "anonymous": "",
        "source": "test",
        "check_count": 1,
        "last_status": True,
        "last_time": "2024-01-01 00:00:00",
    })


# ---------------------------------------------------------------------------
# 1. Proxy model tests
# ---------------------------------------------------------------------------

def testProxyProtocolField():
    """Proxy.protocol 字段默认值、setter、以及非法值回退"""
    p = Proxy("1.2.3.4:1080")
    assert p.protocol == "http"

    for proto in PROXY_PROTOCOLS:
        p2 = Proxy("1.2.3.4:1080", protocol=proto)
        assert p2.protocol == proto

    # invalid value falls back to "http"
    p3 = Proxy("1.2.3.4:1080", protocol="ftp")
    assert p3.protocol == "http"

    p4 = Proxy("1.2.3.4:1080")
    p4.protocol = "socks5"
    assert p4.protocol == "socks5"
    p4.protocol = "invalid"
    assert p4.protocol == "http"

    print("testProxyProtocolField ok!")


def testProxyToDict():
    """to_dict 包含 protocol 字段"""
    for proto in PROXY_PROTOCOLS:
        p = Proxy("1.2.3.4:1080", protocol=proto)
        d = p.to_dict
        assert "protocol" in d
        assert d["protocol"] == proto
    print("testProxyToDict ok!")


def testProxyCreateFromJson():
    """createFromJson 正确恢复 protocol 字段"""
    for proto in PROXY_PROTOCOLS:
        raw = _make_json(protocol=proto)
        p = Proxy.createFromJson(raw)
        assert p.protocol == proto

    # 旧数据（无 protocol 字段）默认 http
    old = json.dumps({"proxy": "1.2.3.4:8080", "https": False, "fail_count": 0,
                      "region": "", "anonymous": "", "source": "",
                      "check_count": 0, "last_status": "", "last_time": ""})
    p2 = Proxy.createFromJson(old)
    assert p2.protocol == "http"
    print("testProxyCreateFromJson ok!")


# ---------------------------------------------------------------------------
# 2. Format validator
# ---------------------------------------------------------------------------

def testFormatValidator():
    """IP 格式验证对 SOCKS 代理地址同样适用（格式相同）"""
    assert formatValidator("1.2.3.4:1080") is True
    assert formatValidator("255.255.255.255:65535") is True
    assert formatValidator("user:pass@1.2.3.4:1080") is True
    assert formatValidator("not_an_ip") is False
    assert formatValidator("1.2.3.4") is False
    print("testFormatValidator ok!")


# ---------------------------------------------------------------------------
# 3. Validator list registration
# ---------------------------------------------------------------------------

def testSocksValidatorLists():
    """ProxyValidator 中 socks4/4a/5 列表均已注册验证函数"""
    assert len(ProxyValidator.socks4_validator) > 0
    assert len(ProxyValidator.socks4a_validator) > 0
    assert len(ProxyValidator.socks5_validator) > 0
    print("testSocksValidatorLists ok!")


# ---------------------------------------------------------------------------
# 4. Individual SOCKS validator functions (mocked network)
# ---------------------------------------------------------------------------

def _mock_response(status_code=200):
    r = MagicMock()
    r.status_code = status_code
    return r


def testSocks4ValidatorSuccess():
    """socks4TimeOutValidator 成功路径"""
    from helper.validator import socks4TimeOutValidator
    with patch("helper.validator.head", return_value=_mock_response(200)) as mock_head:
        result = socks4TimeOutValidator("1.2.3.4:1080")
    assert result is True
    call_kwargs = mock_head.call_args
    proxies_arg = call_kwargs[1].get("proxies") or call_kwargs[0][1]
    assert "socks4://" in proxies_arg.get("http", "")
    print("testSocks4ValidatorSuccess ok!")


def testSocks4ValidatorFailure():
    """socks4TimeOutValidator 失败路径（异常）"""
    from helper.validator import socks4TimeOutValidator
    with patch("helper.validator.head", side_effect=Exception("timeout")):
        result = socks4TimeOutValidator("1.2.3.4:1080")
    assert result is False
    print("testSocks4ValidatorFailure ok!")


def testSocks4aValidatorSuccess():
    """socks4aTimeOutValidator 成功路径"""
    from helper.validator import socks4aTimeOutValidator
    with patch("helper.validator.head", return_value=_mock_response(200)) as mock_head:
        result = socks4aTimeOutValidator("1.2.3.4:1080")
    assert result is True
    call_kwargs = mock_head.call_args
    proxies_arg = call_kwargs[1].get("proxies") or call_kwargs[0][1]
    assert "socks4a://" in proxies_arg.get("http", "")
    print("testSocks4aValidatorSuccess ok!")


def testSocks5ValidatorSuccess():
    """socks5TimeOutValidator 成功路径"""
    from helper.validator import socks5TimeOutValidator
    with patch("helper.validator.head", return_value=_mock_response(200)) as mock_head:
        result = socks5TimeOutValidator("1.2.3.4:1080")
    assert result is True
    call_kwargs = mock_head.call_args
    proxies_arg = call_kwargs[1].get("proxies") or call_kwargs[0][1]
    assert "socks5://" in proxies_arg.get("http", "")
    print("testSocks5ValidatorSuccess ok!")


def testSocks5ValidatorNon200():
    """socks5TimeOutValidator 返回非200状态码"""
    from helper.validator import socks5TimeOutValidator
    with patch("helper.validator.head", return_value=_mock_response(403)):
        result = socks5TimeOutValidator("1.2.3.4:1080")
    assert result is False
    print("testSocks5ValidatorNon200 ok!")


# ---------------------------------------------------------------------------
# 5. DB filter helper (_filter_by_type) — unit-test without Redis
# ---------------------------------------------------------------------------

def testRedisClientFilterByType():
    """RedisClient._filter_by_type 按协议正确过滤"""
    from db.redisClient import RedisClient

    items = [
        _make_json("1.1.1.1:8080", "http", False),
        _make_json("2.2.2.2:8080", "http", True),
        _make_json("3.3.3.3:1080", "socks4", False),
        _make_json("4.4.4.4:1080", "socks4a", False),
        _make_json("5.5.5.5:1080", "socks5", True),
    ]

    # Instantiate without connecting to Redis by patching __init__
    client = RedisClient.__new__(RedisClient)

    assert len(client._filter_by_type(items, "https")) == 2
    assert len(client._filter_by_type(items, "socks4")) == 1
    assert len(client._filter_by_type(items, "socks4a")) == 1
    assert len(client._filter_by_type(items, "socks5")) == 1
    assert len(client._filter_by_type(items, "http")) == 2
    print("testRedisClientFilterByType ok!")


# ---------------------------------------------------------------------------
# 6. DoValidator.validator protocol detection (mocked)
# ---------------------------------------------------------------------------

def testDoValidatorDetectsSocks5():
    """DoValidator.validator 在HTTP失败时检测到SOCKS5协议"""
    from helper.check import DoValidator

    proxy = Proxy("1.2.3.4:1080")

    with patch.object(DoValidator, 'httpValidator', return_value=False), \
         patch.object(DoValidator, 'socks5Validator', return_value=True), \
         patch.object(DoValidator, 'socks5HttpsValidator', return_value=True), \
         patch.object(DoValidator, 'regionGetter', return_value=""):
        result = DoValidator.validator(proxy, "use")

    assert result.protocol == "socks5"
    assert result.last_status is True
    assert result.https is True
    print("testDoValidatorDetectsSocks5 ok!")


def testDoValidatorDetectsSocks4a():
    """DoValidator.validator 在HTTP/SOCKS5失败时检测到SOCKS4a协议"""
    from helper.check import DoValidator

    proxy = Proxy("1.2.3.4:1080")

    with patch.object(DoValidator, 'httpValidator', return_value=False), \
         patch.object(DoValidator, 'socks5Validator', return_value=False), \
         patch.object(DoValidator, 'socks4aValidator', return_value=True), \
         patch.object(DoValidator, 'socks4aHttpsValidator', return_value=False), \
         patch.object(DoValidator, 'regionGetter', return_value=""):
        result = DoValidator.validator(proxy, "use")

    assert result.protocol == "socks4a"
    assert result.last_status is True
    assert result.https is False
    print("testDoValidatorDetectsSocks4a ok!")


def testDoValidatorDetectsSocks4():
    """DoValidator.validator 在HTTP/SOCKS5/SOCKS4a失败时检测到SOCKS4协议"""
    from helper.check import DoValidator

    proxy = Proxy("1.2.3.4:1080")

    with patch.object(DoValidator, 'httpValidator', return_value=False), \
         patch.object(DoValidator, 'socks5Validator', return_value=False), \
         patch.object(DoValidator, 'socks4aValidator', return_value=False), \
         patch.object(DoValidator, 'socks4Validator', return_value=True), \
         patch.object(DoValidator, 'regionGetter', return_value=""):
        result = DoValidator.validator(proxy, "use")

    assert result.protocol == "socks4"
    assert result.last_status is True
    assert result.https is False
    print("testDoValidatorDetectsSocks4 ok!")


def testDoValidatorAllFail():
    """DoValidator.validator 所有协议检测失败"""
    from helper.check import DoValidator

    proxy = Proxy("1.2.3.4:1080")

    with patch.object(DoValidator, 'httpValidator', return_value=False), \
         patch.object(DoValidator, 'socks5Validator', return_value=False), \
         patch.object(DoValidator, 'socks4aValidator', return_value=False), \
         patch.object(DoValidator, 'socks4Validator', return_value=False):
        result = DoValidator.validator(proxy, "use")

    assert result.last_status is False
    assert result.fail_count == 1
    print("testDoValidatorAllFail ok!")


def testDoValidatorHttpProxy():
    """DoValidator.validator HTTP代理保持http协议"""
    from helper.check import DoValidator

    proxy = Proxy("1.2.3.4:8080")

    with patch.object(DoValidator, 'httpValidator', return_value=True), \
         patch.object(DoValidator, 'httpsValidator', return_value=True), \
         patch.object(DoValidator, 'regionGetter', return_value=""):
        result = DoValidator.validator(proxy, "use")

    assert result.protocol == "http"
    assert result.last_status is True
    assert result.https is True
    print("testDoValidatorHttpProxy ok!")


# ---------------------------------------------------------------------------
# 7. API get_raw scheme selection
# ---------------------------------------------------------------------------

def testGetRawScheme():
    """get_raw 根据 protocol 字段返回正确的 scheme"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from api.proxyApi import app

    app.config['TESTING'] = True
    client = app.test_client()

    for proto in ("socks4", "socks4a", "socks5"):
        p = Proxy("1.2.3.4:1080", protocol=proto)
        with patch("api.proxyApi.proxy_handler") as mock_handler:
            mock_handler.get.return_value = p
            resp = client.get("/get_raw/")
        assert resp.status_code == 200
        body = resp.data.decode()
        assert body == "{}://1.2.3.4:1080".format(proto), \
            "Expected {}://1.2.3.4:1080, got {}".format(proto, body)

    # HTTP proxy with HTTPS support
    p_http = Proxy("2.2.2.2:8080", protocol="http", https=True)
    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.get.return_value = p_http
        resp = client.get("/get_raw/")
    assert resp.data.decode() == "https://2.2.2.2:8080"

    # HTTP proxy without HTTPS
    p_plain = Proxy("3.3.3.3:8080", protocol="http", https=False)
    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.get.return_value = p_plain
        resp = client.get("/get_raw/")
    assert resp.data.decode() == "http://3.3.3.3:8080"

    print("testGetRawScheme ok!")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def runAllTests():
    testProxyProtocolField()
    testProxyToDict()
    testProxyCreateFromJson()
    testFormatValidator()
    testSocksValidatorLists()
    testSocks4ValidatorSuccess()
    testSocks4ValidatorFailure()
    testSocks4aValidatorSuccess()
    testSocks5ValidatorSuccess()
    testSocks5ValidatorNon200()
    testRedisClientFilterByType()
    testDoValidatorDetectsSocks5()
    testDoValidatorDetectsSocks4a()
    testDoValidatorDetectsSocks4()
    testDoValidatorAllFail()
    testDoValidatorHttpProxy()
    testGetRawScheme()
    print("\nAll SOCKS support tests passed!")


if __name__ == '__main__':
    runAllTests()
