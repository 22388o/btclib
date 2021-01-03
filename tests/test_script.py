#!/usr/bin/env python3

# Copyright (C) 2017-2021 The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

"Tests for the `btclib.script` module."

from typing import List

import pytest

from btclib import script
from btclib.exceptions import BTClibValueError


def test_operators() -> None:
    for i in script.OP_CODE_NAMES:
        b = script.OP_CODES[script.OP_CODE_NAMES[i]]
        assert i == b[0]
    for name in script.OP_CODES:
        # skip duplicated
        if name in ("OP_FALSE", "OP_TRUE", "OP_NOP2", "OP_NOP3"):
            continue
        i = script.OP_CODES[name][0]
        assert name == script.OP_CODE_NAMES[i]
    for i in range(76, 186):
        # skip disabled 'splice' opcodes
        if i in (126, 127, 128, 129):
            continue
        # skip disabled 'bitwise logic' opcodes
        if i in (131, 132, 133, 134):
            continue
        # skip disabled 'splice' opcodes
        if i in (141, 142, 149, 150, 151, 152, 152, 153):
            continue
        # skip 'reserved' opcodes
        if i in (80, 98, 101, 102, 137, 138):
            continue
        assert i in script.OP_CODE_NAMES.keys()


def test_simple() -> None:
    script_list: List[List[script.ScriptToken]] = [
        [2, 3, "OP_ADD", 5, "OP_EQUAL"],
        ["1ADD", "OP_1ADD", "1ADE", "OP_EQUAL"],
        [hex(26)[2:].upper(), -1, "OP_ADD", hex(26)[2:].upper(), "OP_EQUAL"],
        [
            hex(0xFFFFFFFF)[2:].upper(),
            -1,
            "OP_ADD",
            hex(0xFFFFFFFF)[2:].upper(),
            "OP_EQUAL",
        ],
        ["1F" * 250, "OP_DROP"],
        ["1F" * 520, "OP_DROP"],
    ]
    for script_pub_key in script_list:
        assert script_pub_key == script.parse(script.serialize(script_pub_key))
        assert script_pub_key == script.parse(script.serialize(script_pub_key).hex())


def test_exceptions() -> None:

    script_pub_key: List[script.ScriptToken] = [2, 3, "OP_ADD", 5, "OP_RETURN_244"]
    err_msg = "invalid string token: OP_RETURN_244"
    with pytest.raises(BTClibValueError, match=err_msg):
        script.serialize(script_pub_key)

    with pytest.raises(TypeError):
        script.serialize([2, 3, "OP_ADD", 5, script.serialize])  # type: ignore

    err_msg = "Too many bytes for OP_PUSHDATA: "
    with pytest.raises(BTClibValueError, match=err_msg):
        script_pub_key = ["1f" * 521, "OP_DROP"]
        script.serialize(script_pub_key)

    # A script_pub_key with OP_PUSHDATA4 can be decoded
    script_bytes = "4e09020000" + "00" * 521 + "75"  # ['00'*521, 'OP_DROP']
    script_pub_key_ = script.parse(script_bytes)
    # but it cannot be encoded
    err_msg = "Too many bytes for OP_PUSHDATA: "
    with pytest.raises(BTClibValueError, match=err_msg):
        script.serialize(script_pub_key_)


def test_nulldata() -> None:

    scripts: List[List[script.ScriptToken]] = [
        ["OP_RETURN", "11" * 79],
        ["OP_RETURN", "00" * 79],
    ]
    for script_pub_key in scripts:
        assert script_pub_key == script.parse(script.serialize(script_pub_key))
        assert script_pub_key == script.parse(script.serialize(script_pub_key).hex())


def test_op_int() -> None:
    i = 0b01111111
    assert len(script._op_int(i)) == 2  # pylint: disable=protected-access
    i = 0b11111111
    assert len(script._op_int(i)) == 3  # pylint: disable=protected-access
    i = 0b0111111111111111
    assert len(script._op_int(i)) == 3  # pylint: disable=protected-access
    i = 0b1111111111111111
    assert len(script._op_int(i)) == 4  # pylint: disable=protected-access


def test_op_pushdata() -> None:
    length = 75
    b = "00" * length
    assert len(script._op_pushdata(b)) == length + 1  # pylint: disable=protected-access
    b = "00" * (length + 1)
    assert (  # pylint: disable=protected-access
        len(script._op_pushdata(b)) == (length + 1) + 2
    )

    length = 255
    b = "00" * length
    assert len(script._op_pushdata(b)) == length + 2  # pylint: disable=protected-access
    b = "00" * (length + 1)
    assert (  # pylint: disable=protected-access
        len(script._op_pushdata(b)) == (length + 1) + 3
    )


def test_encoding():
    script_bytes = b"jKBIP141 \\o/ Hello SegWit :-) keep it strong! LLAP Bitcoin twitter.com/khs9ne"
    assert script.serialize(script.parse(script_bytes)) == script_bytes