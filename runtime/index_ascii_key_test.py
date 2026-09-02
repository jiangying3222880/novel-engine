#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1-5 拼音碰撞消歧测试：验证 index._ascii_key 对：
  ① 不同中文名 → id 全局唯一（拼音碰撞时后出现者加码点后缀）
  ② 同一中文名 → 幂等（永远返回同一键）
  ③ id 恒为纯 ASCII 且不含 /
碰撞例子：陈晨 / 晨尘 均为 chenchen；沈青梧 / 沈青吾 均为 shenqingwu。
运行：python runtime/index_ascii_key_test.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "deps"))
import index


def reset():
    index.ENTITY_ID_MAP.clear()
    index._ASCII_OWNERS.clear()
    index._ASCII_WARNED.clear()


def test_plain_no_collision():
    assert index._ascii_key("陌无尘") == "mowuchen", "无碰撞名应保持纯拼音键"
    assert index._ascii_key("方若华") == "fangruohua", "无碰撞名应保持纯拼音键"


def test_collision_disambiguated():
    k1 = index._ascii_key("陈晨")
    k2 = index._ascii_key("晨尘")
    assert k1 == "chenchen"
    assert k2 != k1, "拼音碰撞必须消歧"
    assert k2 == "chenchen_" + index._disambiguate_suffix("晨尘")


def test_collision_reciprocal():
    # 交换出现顺序，两键仍互不相同；先出现者用纯键
    a1 = index._ascii_key("晨尘")
    a2 = index._ascii_key("陈晨")
    assert a1 == "chenchen"
    assert a2 != a1
    assert a2 == "chenchen_" + index._disambiguate_suffix("陈晨")


def test_idempotent():
    index._ascii_key("陈晨")
    index._ascii_key("晨尘")
    assert index._ascii_key("陈晨") == "chenchen"
    assert index._ascii_key("晨尘") == "chenchen_" + index._disambiguate_suffix("晨尘")


def test_triplet_unique():
    # 三个都读 chen 开头的不同全名，id 全部互异
    keys = [index._ascii_key(n) for n in ("陈晨", "晨尘", "尘晨")]
    assert len(set(keys)) == len(keys), "三个同拼名 id 必须两两不同"


def test_doc_id_unique():
    d1 = index._doc_id("truth", "陈晨", 0)
    d2 = index._doc_id("truth", "晨尘", 0)
    assert d1 != d2, "doc_id 不得互相覆盖"


def test_all_ascii_no_slash():
    for name in ("陈晨", "晨尘", "沈青梧", "沈青吾", "方若华", "方若桦", "陌无尘"):
        k = index._ascii_key(name)
        assert "/" not in k, f"id 不得含 /: {name}->{k}"
        assert re.fullmatch(r"[A-Za-z0-9_.\-]+", k), f"id 必须纯 ASCII: {name}->{k}"


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]


def main():
    fails = 0
    for fn in TESTS:
        reset()
        try:
            fn()
            print(f"  ✓ {fn.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"  ✗ {fn.__name__}: {e}")
    total = len(TESTS) - fails
    print(f"\n{total}/{len(TESTS)} 通过")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())