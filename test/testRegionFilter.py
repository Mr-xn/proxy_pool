# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     testRegionFilter
   Description :   region模糊过滤单元测试
   Author :        JHao
   date：          2024/1/1
-------------------------------------------------
   Change Activity:
                   2024/01/01: 新增region过滤测试
-------------------------------------------------
"""
__author__ = 'JHao'

import json
from unittest.mock import patch, MagicMock
from helper.proxy import Proxy


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_proxy(ip, region, protocol="http", https=False):
    """Build a Proxy object with the given region."""
    return Proxy(ip, region=region, protocol=protocol, https=https,
                 source="test", check_count=1, last_status=True,
                 last_time="2024-01-01 00:00:00")


def _make_json(ip, region, protocol="http", https=False):
    """Build the JSON string stored in Redis for a proxy."""
    return json.dumps({
        "proxy": ip,
        "https": https,
        "protocol": protocol,
        "fail_count": 0,
        "region": region,
        "anonymous": "",
        "source": "test",
        "check_count": 1,
        "last_status": True,
        "last_time": "2024-01-01 00:00:00",
    })


# Pool of sample proxies with various regions
SAMPLE_PROXIES = [
    _make_proxy("1.1.1.1:8080", "China Beijing"),
    _make_proxy("2.2.2.2:8080", "China Shanghai"),
    _make_proxy("3.3.3.3:8080", "United States New York"),
    _make_proxy("4.4.4.4:8080", "Japan Tokyo"),
    _make_proxy("5.5.5.5:8080", "中国 广东 深圳"),
    _make_proxy("6.6.6.6:8080", "CN Guangzhou"),
    _make_proxy("7.7.7.7:8080", ""),            # no region info
    _make_proxy("8.8.8.8:8080", "CHINA Hong Kong"),
]


# ---------------------------------------------------------------------------
# 1. _filter_by_region – unit tests on the static helper directly
# ---------------------------------------------------------------------------

def testFilterByRegionInclude():
    """region= filters: only matching proxies remain."""
    from handler.proxyHandler import ProxyHandler
    f = ProxyHandler._filter_by_region

    # "china" should match "China Beijing", "China Shanghai",
    # "中国 广东 深圳" does NOT contain "china", "CN Guangzhou" does NOT,
    # "CHINA Hong Kong" DOES (case-insensitive)
    result = f(SAMPLE_PROXIES, region="china")
    ips = {p.proxy for p in result}
    assert "1.1.1.1:8080" in ips, "China Beijing should match"
    assert "2.2.2.2:8080" in ips, "China Shanghai should match"
    assert "8.8.8.8:8080" in ips, "CHINA Hong Kong should match (case-insensitive)"
    assert "3.3.3.3:8080" not in ips, "US proxy should not match"
    assert "4.4.4.4:8080" not in ips, "Japan proxy should not match"
    print("testFilterByRegionInclude ok!")


def testFilterByRegionIncludeChinese():
    """region= with Chinese keyword '中国' matches correctly."""
    from handler.proxyHandler import ProxyHandler
    f = ProxyHandler._filter_by_region

    result = f(SAMPLE_PROXIES, region="中国")
    ips = {p.proxy for p in result}
    assert "5.5.5.5:8080" in ips, "Chinese region string should match"
    assert "1.1.1.1:8080" not in ips, "English 'China' should not match '中国' keyword"
    print("testFilterByRegionIncludeChinese ok!")


def testFilterByRegionIncludeCN():
    """region= with 'CN' matches proxies whose region contains 'cn' (case-insensitive)."""
    from handler.proxyHandler import ProxyHandler
    f = ProxyHandler._filter_by_region

    result = f(SAMPLE_PROXIES, region="CN")
    ips = {p.proxy for p in result}
    assert "6.6.6.6:8080" in ips, "CN Guangzhou should match"
    # "China Beijing" contains "cn"? No — "china" does not start with "cn" as substring... wait:
    # "China Beijing".lower() = "china beijing" — does not contain "cn"
    # "CN Guangzhou".lower() = "cn guangzhou" — contains "cn"
    assert "1.1.1.1:8080" not in ips, "'China Beijing' does not contain the substring 'cn'"
    print("testFilterByRegionIncludeCN ok!")


def testFilterByRegionExclude():
    """exclude_region= filters out matching proxies."""
    from handler.proxyHandler import ProxyHandler
    f = ProxyHandler._filter_by_region

    result = f(SAMPLE_PROXIES, exclude_region="china")
    ips = {p.proxy for p in result}
    assert "1.1.1.1:8080" not in ips, "China Beijing should be excluded"
    assert "2.2.2.2:8080" not in ips, "China Shanghai should be excluded"
    assert "8.8.8.8:8080" not in ips, "CHINA Hong Kong should be excluded"
    assert "3.3.3.3:8080" in ips, "US proxy should remain"
    assert "4.4.4.4:8080" in ips, "Japan proxy should remain"
    print("testFilterByRegionExclude ok!")


def testFilterByRegionBoth():
    """region= and exclude_region= can be used simultaneously."""
    from handler.proxyHandler import ProxyHandler
    f = ProxyHandler._filter_by_region

    # Include United States, exclude New York
    proxies = [
        _make_proxy("10.0.0.1:8080", "United States New York"),
        _make_proxy("10.0.0.2:8080", "United States Los Angeles"),
        _make_proxy("10.0.0.3:8080", "China Beijing"),
    ]
    result = f(proxies, region="united states", exclude_region="new york")
    ips = {p.proxy for p in result}
    assert "10.0.0.2:8080" in ips
    assert "10.0.0.1:8080" not in ips
    assert "10.0.0.3:8080" not in ips
    print("testFilterByRegionBoth ok!")


def testFilterByRegionNone():
    """No filter params: all proxies returned unchanged."""
    from handler.proxyHandler import ProxyHandler
    f = ProxyHandler._filter_by_region

    result = f(SAMPLE_PROXIES)
    assert len(result) == len(SAMPLE_PROXIES)
    print("testFilterByRegionNone ok!")


def testFilterByRegionEmptyPool():
    """Empty proxy list returns empty list."""
    from handler.proxyHandler import ProxyHandler
    f = ProxyHandler._filter_by_region

    assert f([], region="china") == []
    assert f([], exclude_region="china") == []
    print("testFilterByRegionEmptyPool ok!")


def testFilterByRegionNoMatch():
    """region= that matches nothing returns empty list."""
    from handler.proxyHandler import ProxyHandler
    f = ProxyHandler._filter_by_region

    result = f(SAMPLE_PROXIES, region="zzz_no_match_zzz")
    assert result == []
    print("testFilterByRegionNoMatch ok!")


def testFilterByRegionExcludeAll():
    """exclude_region= that matches everything returns empty list."""
    from handler.proxyHandler import ProxyHandler
    f = ProxyHandler._filter_by_region

    # all proxies have a region that contains '.' (none do actually) — use empty string
    # use a keyword present in ALL non-empty regions
    proxies = [
        _make_proxy("a:1", "China"),
        _make_proxy("b:2", "China"),
    ]
    result = f(proxies, exclude_region="china")
    assert result == []
    print("testFilterByRegionExcludeAll ok!")


def testFilterByRegionEmptyRegionField():
    """Proxies with empty region field are excluded by region= and kept by exclude_region=."""
    from handler.proxyHandler import ProxyHandler
    f = ProxyHandler._filter_by_region

    proxies = [
        _make_proxy("a:1", ""),
        _make_proxy("b:2", "China"),
    ]
    include_result = f(proxies, region="china")
    assert len(include_result) == 1 and include_result[0].proxy == "b:2"

    exclude_result = f(proxies, exclude_region="china")
    assert len(exclude_result) == 1 and exclude_result[0].proxy == "a:1"

    print("testFilterByRegionEmptyRegionField ok!")


# ---------------------------------------------------------------------------
# 2. ProxyHandler.get / pop / getAll integration (mock DB)
# ---------------------------------------------------------------------------

def _build_handler_with_proxies(proxy_objects):
    """Return a ProxyHandler whose DB is mocked to yield proxy_objects."""
    from handler.proxyHandler import ProxyHandler
    handler = ProxyHandler.__new__(ProxyHandler)
    handler.db = MagicMock()
    handler.db.getAll.return_value = [p.to_json for p in proxy_objects]
    handler.db.get.return_value = proxy_objects[0].to_json if proxy_objects else None
    handler.db.pop.return_value = proxy_objects[0].to_json if proxy_objects else None
    return handler


def testHandlerGetAllWithRegion():
    """ProxyHandler.getAll filters by region correctly."""
    handler = _build_handler_with_proxies(SAMPLE_PROXIES)
    result = handler.getAll(region="china")
    ips = {p.proxy for p in result}
    assert "1.1.1.1:8080" in ips
    assert "3.3.3.3:8080" not in ips
    print("testHandlerGetAllWithRegion ok!")


def testHandlerGetAllWithExcludeRegion():
    """ProxyHandler.getAll excludes by region correctly."""
    handler = _build_handler_with_proxies(SAMPLE_PROXIES)
    result = handler.getAll(exclude_region="china")
    ips = {p.proxy for p in result}
    assert "1.1.1.1:8080" not in ips
    assert "3.3.3.3:8080" in ips
    print("testHandlerGetAllWithExcludeRegion ok!")


def testHandlerGetWithRegion():
    """ProxyHandler.get returns a proxy from the matching region."""
    handler = _build_handler_with_proxies(SAMPLE_PROXIES)
    proxy = handler.get(region="japan")
    assert proxy is not None
    assert "japan" in proxy.region.lower()
    print("testHandlerGetWithRegion ok!")


def testHandlerGetWithRegionNoMatch():
    """ProxyHandler.get returns None when no proxy matches."""
    handler = _build_handler_with_proxies(SAMPLE_PROXIES)
    proxy = handler.get(region="zzz_no_match_zzz")
    assert proxy is None
    print("testHandlerGetWithRegionNoMatch ok!")


def testHandlerPopWithRegion():
    """ProxyHandler.pop deletes and returns a matching proxy."""
    handler = _build_handler_with_proxies(SAMPLE_PROXIES)
    proxy = handler.pop(region="japan")
    assert proxy is not None
    assert "japan" in proxy.region.lower()
    handler.db.delete.assert_called_once_with(proxy.proxy)
    print("testHandlerPopWithRegion ok!")


def testHandlerPopWithRegionNoMatch():
    """ProxyHandler.pop returns None when no proxy matches."""
    handler = _build_handler_with_proxies(SAMPLE_PROXIES)
    proxy = handler.pop(region="zzz_no_match_zzz")
    assert proxy is None
    handler.db.delete.assert_not_called()
    print("testHandlerPopWithRegionNoMatch ok!")


# ---------------------------------------------------------------------------
# 3. API-level tests (Flask test client)
# ---------------------------------------------------------------------------

def _build_api_client(proxy_objects):
    """Return a Flask test client with proxy_handler mocked."""
    from api.proxyApi import app
    app.config['TESTING'] = True
    client = app.test_client()
    return client


def testApiGetWithRegion():
    """GET /get/?region=china returns a proxy from China."""
    from handler.proxyHandler import ProxyHandler

    china_proxy = _make_proxy("1.1.1.1:8080", "China Beijing")
    us_proxy = _make_proxy("3.3.3.3:8080", "United States")

    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.get.return_value = china_proxy

        from api.proxyApi import app
        app.config['TESTING'] = True
        client = app.test_client()
        resp = client.get("/get/?region=china")

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["proxy"] == "1.1.1.1:8080"
    # Verify region and exclude_region were passed to handler.get
    mock_handler.get.assert_called_once_with(None, region="china", exclude_region=None)
    print("testApiGetWithRegion ok!")


def testApiGetWithExcludeRegion():
    """GET /get/?exclude_region=CN returns a non-CN proxy."""
    us_proxy = _make_proxy("3.3.3.3:8080", "United States")

    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.get.return_value = us_proxy

        from api.proxyApi import app
        app.config['TESTING'] = True
        client = app.test_client()
        resp = client.get("/get/?exclude_region=CN")

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["proxy"] == "3.3.3.3:8080"
    mock_handler.get.assert_called_once_with(None, region=None, exclude_region="CN")
    print("testApiGetWithExcludeRegion ok!")


def testApiGetRawWithRegion():
    """GET /get_raw/?region=japan returns correct raw proxy string."""
    japan_proxy = _make_proxy("4.4.4.4:1080", "Japan Tokyo", protocol="socks5")

    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.get.return_value = japan_proxy

        from api.proxyApi import app
        app.config['TESTING'] = True
        client = app.test_client()
        resp = client.get("/get_raw/?region=japan")

    assert resp.status_code == 200
    assert resp.data.decode() == "socks5://4.4.4.4:1080"
    mock_handler.get.assert_called_once_with(None, region="japan", exclude_region=None)
    print("testApiGetRawWithRegion ok!")


def testApiGetRawNoProxy():
    """GET /get_raw/?region=zzz returns 'no proxy' when nothing matches."""
    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.get.return_value = None

        from api.proxyApi import app
        app.config['TESTING'] = True
        client = app.test_client()
        resp = client.get("/get_raw/?region=zzz")

    assert resp.status_code == 200
    assert resp.data.decode() == "no proxy"
    print("testApiGetRawNoProxy ok!")


def testApiAllWithRegion():
    """GET /all/?region=china returns only matching proxies."""
    china_proxies = [
        _make_proxy("1.1.1.1:8080", "China Beijing"),
        _make_proxy("2.2.2.2:8080", "China Shanghai"),
    ]

    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.getAll.return_value = china_proxies

        from api.proxyApi import app
        app.config['TESTING'] = True
        client = app.test_client()
        resp = client.get("/all/?region=china")

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 2
    ips = {d["proxy"] for d in data}
    assert "1.1.1.1:8080" in ips
    assert "2.2.2.2:8080" in ips
    mock_handler.getAll.assert_called_once_with(None, region="china", exclude_region=None)
    print("testApiAllWithRegion ok!")


def testApiAllWithExcludeRegion():
    """GET /all/?exclude_region=china returns only non-China proxies."""
    non_china = [_make_proxy("3.3.3.3:8080", "United States")]

    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.getAll.return_value = non_china

        from api.proxyApi import app
        app.config['TESTING'] = True
        client = app.test_client()
        resp = client.get("/all/?exclude_region=china")

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 1
    assert data[0]["proxy"] == "3.3.3.3:8080"
    mock_handler.getAll.assert_called_once_with(None, region=None, exclude_region="china")
    print("testApiAllWithExcludeRegion ok!")


def testApiAllWithTypeAndRegion():
    """GET /all/?type=socks5&region=china combines both filters."""
    socks5_china = [_make_proxy("5.5.5.5:1080", "China", protocol="socks5")]

    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.getAll.return_value = socks5_china

        from api.proxyApi import app
        app.config['TESTING'] = True
        client = app.test_client()
        resp = client.get("/all/?type=socks5&region=china")

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 1
    mock_handler.getAll.assert_called_once_with("socks5", region="china", exclude_region=None)
    print("testApiAllWithTypeAndRegion ok!")


def testApiPopWithRegion():
    """GET /pop/?region=china returns and would delete a China proxy."""
    china_proxy = _make_proxy("1.1.1.1:8080", "China")

    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.pop.return_value = china_proxy

        from api.proxyApi import app
        app.config['TESTING'] = True
        client = app.test_client()
        resp = client.get("/pop/?region=china")

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["proxy"] == "1.1.1.1:8080"
    mock_handler.pop.assert_called_once_with(None, region="china", exclude_region=None)
    print("testApiPopWithRegion ok!")


def testApiGetRegionCaseInsensitive():
    """GET /get/?region= is case-insensitive in both kwarg passing and handler matching."""
    # The API passes the raw string (preserving case), and the handler does .lower()
    # comparison. Test that a mixed-case region keyword is passed through unchanged.
    proxy = _make_proxy("1.1.1.1:8080", "China Beijing")

    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.get.return_value = proxy

        from api.proxyApi import app
        app.config['TESTING'] = True
        client = app.test_client()
        resp = client.get("/get/?region=CHINA")

    mock_handler.get.assert_called_once_with(None, region="CHINA", exclude_region=None)
    print("testApiGetRegionCaseInsensitive ok!")


def testApiGetEmptyRegionIgnored():
    """GET /get/?region= (empty string) is treated as no filter."""
    proxy = _make_proxy("1.1.1.1:8080", "China Beijing")

    with patch("api.proxyApi.proxy_handler") as mock_handler:
        mock_handler.get.return_value = proxy

        from api.proxyApi import app
        app.config['TESTING'] = True
        client = app.test_client()
        resp = client.get("/get/?region=")

    # Empty region string should be normalized to None
    mock_handler.get.assert_called_once_with(None, region=None, exclude_region=None)
    print("testApiGetEmptyRegionIgnored ok!")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def runAllTests():
    testFilterByRegionInclude()
    testFilterByRegionIncludeChinese()
    testFilterByRegionIncludeCN()
    testFilterByRegionExclude()
    testFilterByRegionBoth()
    testFilterByRegionNone()
    testFilterByRegionEmptyPool()
    testFilterByRegionNoMatch()
    testFilterByRegionExcludeAll()
    testFilterByRegionEmptyRegionField()
    testHandlerGetAllWithRegion()
    testHandlerGetAllWithExcludeRegion()
    testHandlerGetWithRegion()
    testHandlerGetWithRegionNoMatch()
    testHandlerPopWithRegion()
    testHandlerPopWithRegionNoMatch()
    testApiGetWithRegion()
    testApiGetWithExcludeRegion()
    testApiGetRawWithRegion()
    testApiGetRawNoProxy()
    testApiAllWithRegion()
    testApiAllWithExcludeRegion()
    testApiAllWithTypeAndRegion()
    testApiPopWithRegion()
    testApiGetRegionCaseInsensitive()
    testApiGetEmptyRegionIgnored()
    print("\nAll region filter tests passed!")


if __name__ == '__main__':
    runAllTests()
