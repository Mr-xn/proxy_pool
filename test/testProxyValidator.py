# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     testProxyValidator
   Description :
   Author :        JHao
   date：          2021/5/25
-------------------------------------------------
   Change Activity:
                   2021/5/25:
                   2024/01/01: 新增socks4/socks4a/socks5 validator测试
-------------------------------------------------
"""
__author__ = 'JHao'

from helper.validator import ProxyValidator


def testProxyValidator():
    print("pre_validator:")
    for _ in ProxyValidator.pre_validator:
        print("  ", _)
    print("http_validator:")
    for _ in ProxyValidator.http_validator:
        print("  ", _)
    print("https_validator:")
    for _ in ProxyValidator.https_validator:
        print("  ", _)
    print("socks4_validator:")
    for _ in ProxyValidator.socks4_validator:
        print("  ", _)
    print("socks4a_validator:")
    for _ in ProxyValidator.socks4a_validator:
        print("  ", _)
    print("socks5_validator:")
    for _ in ProxyValidator.socks5_validator:
        print("  ", _)

    assert len(ProxyValidator.socks4_validator) > 0, "socks4_validator should not be empty"
    assert len(ProxyValidator.socks4a_validator) > 0, "socks4a_validator should not be empty"
    assert len(ProxyValidator.socks5_validator) > 0, "socks5_validator should not be empty"
    print("testProxyValidator ok!")


if __name__ == '__main__':
    testProxyValidator()
