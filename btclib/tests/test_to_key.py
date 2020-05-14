#!/usr/bin/env python3

# Copyright (C) 2017-2020 The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

import copy

from btclib.alias import BIP32KeyDict, INF
from btclib.base58 import b58encode
from btclib.curvemult import mult
from btclib.curves import secp256k1 as ec
from btclib.secpoint import bytes_from_point


def _serialize(d: BIP32KeyDict) -> bytes:
    t = d["version"]
    t += d["depth"].to_bytes(1, "big")
    t += d["parent_fingerprint"]
    t += d["index"]
    t += d["chain_code"]
    t += d["key"]
    return b58encode(t, 78)


q = 12
q_bytes = q.to_bytes(32, byteorder="big")
q_bytes_hexstring = q_bytes.hex()
q_bytes_hexstring2 = " " + q_bytes_hexstring + " "
wifcompressed = b58encode(b"\x80" + q_bytes + b"\x01")
wifcompressed_string = wifcompressed.decode("ascii")
wifcompressed_string2 = " " + wifcompressed_string + " "
wifuncompressed = b58encode(b"\x80" + q_bytes)
wifuncompressed_string = wifuncompressed.decode("ascii")
wifuncompressed_string2 = " " + wifuncompressed_string + " "

xprv_dict: BIP32KeyDict = {
    "version": b"\x04\x88\xAD\xE4",
    "depth": 0,
    "parent_fingerprint": b"\x00\x00\x00\x00",
    "index": b"\x00\x00\x00\x00",
    "chain_code": 32 * b"\x00",
    "key": b"\x00" + q_bytes,
}
xprv = _serialize(xprv_dict)
xprv_string = xprv.decode("ascii")
xprv_string2 = " " + xprv_string + " "


# prv key with no network / compression information
prv_keys = [
    q,
    q_bytes,
    q_bytes_hexstring,
    q_bytes_hexstring2,
]

compressed_prv_keys = [
    wifcompressed,
    wifcompressed_string,
    wifcompressed_string2,
    xprv,
    xprv_string,
    xprv_string2,
    xprv_dict,
]

uncompressed_prv_keys = [
    wifuncompressed,
    wifuncompressed_string,
    wifuncompressed_string2,
]

Q = mult(q)
Q_compressed = bytes_from_point(Q, compressed=True)
Q_compressed_hexstring = Q_compressed.hex()
Q_compressed_hexstring2 = " " + Q_compressed_hexstring + " "
Q_uncompressed = bytes_from_point(Q, compressed=False)
Q_uncompressed_hexstring = Q_uncompressed.hex()
Q_uncompressed_hexstring2 = " " + Q_uncompressed_hexstring + " "

xpub_dict: BIP32KeyDict = {
    "version": b"\x04\x88\xB2\x1E",
    "depth": xprv_dict["depth"],
    "parent_fingerprint": xprv_dict["parent_fingerprint"],
    "index": xprv_dict["index"],
    "chain_code": xprv_dict["chain_code"],
    "key": Q_compressed,
}
xpub = _serialize(xpub_dict)
xpub_string = xpub.decode("ascii")
xpub_string2 = " " + xpub_string + " "

compressed_pub_keys = [
    Q_compressed,
    Q_compressed_hexstring,
    Q_compressed_hexstring2,
    xpub_dict,
    xpub,
    xpub_string,
    xpub_string2,
]

uncompressed_pub_keys = [
    Q_uncompressed,
    Q_uncompressed_hexstring,
    Q_uncompressed_hexstring2,
]

# all bad BIP32 keys
# version / key mismatch
xprv_dict_bad = copy.copy(xpub_dict)
xprv_dict_bad["version"] = b"\x04\x88\xB2\x1E"
xpub_dict_bad = copy.copy(xprv_dict)
xpub_dict_bad["version"] = b"\x04\x88\xAD\xE4"
bad_bip32_keys = [_serialize(xprv_dict_bad), _serialize(xpub_dict_bad)]
# depth_pfp_index mismatch
# key stats with 04
# unknown version

invalid_prv_keys = [
    wifcompressed + b"\x01",
    wifcompressed_string + "01",
    wifuncompressed + b"\x01",
    wifuncompressed_string + "01",
    xprv + b"\x00",
    xprv_string + "00",
    xprv_dict["key"][1:] + b"\x00",
    xprv_dict["key"][1:].hex() + "00",
    xprv_dict["key"],
    xprv_dict["key"].hex(),
    "notakey",
]

invalid_pub_keys = [
    INF,
    b"\x02" + INF[0].to_bytes(32, "big"),
    b"\x04" + INF[0].to_bytes(32, "big") + INF[1].to_bytes(32, "big"),
    # INF as WIF
    # INF as xpub
    # INF as hex-string
]

not_a_prv_keys = [Q] + compressed_pub_keys + uncompressed_pub_keys
not_a_prv_keys += invalid_prv_keys + invalid_pub_keys

not_a_pub_keys = invalid_prv_keys + invalid_pub_keys

# test wrong curve and wrong network
# q in (0, ec.n)

for inv_q in (0, ec.n):
    invalid_prv_keys.append(inv_q)
    inv_q_bytes = inv_q.to_bytes(32, "big")
    t = b"\x80" + inv_q_bytes + b"\x01"
    wif = b58encode(t)
    invalid_prv_keys.append(wif)
    invalid_prv_keys.append(wif.decode("ascii"))
    t = b"\x80" + inv_q_bytes
    wif = b58encode(t)
    invalid_prv_keys.append(wif)
    invalid_prv_keys.append(wif.decode("ascii"))
    t = b"\x04\x88\xAD\xE4"
    t += b"\x00"
    t += b"\x00\x00\x00\x00"
    t += b"\x00\x00\x00\x00"
    t += 32 * b"\x00"
    t += b"\x00" + inv_q_bytes
    xprv_temp = b58encode(t, 78)
    invalid_prv_keys.append(xprv_temp)
    invalid_prv_keys.append(xprv_temp.decode("ascii"))
