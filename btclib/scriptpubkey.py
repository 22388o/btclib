#!/usr/bin/env python3

# Copyright (C) 2017-2020 The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

"""ScriptPubKey functions.

"""

from typing import Iterable, Union, List

from .script import Token
from .utils import Octets


def nulldata_scriptPubKey(data: Octets) -> List[Token]:
    """Return the nulldata scriptPubKey with the provided data."""
    if isinstance(data, str):  # hex string
        data = data.strip()
        data = bytes.fromhex(data)
    if len(data) > 40:
        msg = f"Invalid data lenght ({len(data)} bytes) "
        msg += "for nulldata scriptPubKey"
        raise ValueError(msg)
    return ['OP_RETURN', data.hex()]


def p2pk_scriptPubKey(pubkey: Octets) -> List[Token]:
    """Return the p2pk scriptPubKey of the provided pubkey."""
    if isinstance(pubkey, str):  # hex string
        pubkey = pubkey.strip()
        pubkey = bytes.fromhex(pubkey)
    if len(pubkey) not in (33, 65):
        msg = f"Invalid pubkey lenght ({len(pubkey)} bytes) "
        msg += "for p2pk scriptPubKey"
        raise ValueError(msg)
    return [pubkey.hex(), 'OP_CHECKSIG']


def multisig_scriptPubKey(m: int, pubkeys: Iterable[Octets]) -> List[Token]:
    """Return the m-of-n multi-sig scriptPubKey of the provided pubkeys."""

    if m<1 or m>16:
        raise ValueError(f"Invalid m ({m})")
        # raise ValueError("Impossible m-of-n ({m}-of-{n})")

    scriptPubKey : List[Token] = [m]
    for pubkey in pubkeys:
        if isinstance(pubkey, str):  # hex string
            pubkey = pubkey.strip()
            pubkey = bytes.fromhex(pubkey)
        if len(pubkey) not in (33, 65):
            msg = f"Invalid pubkey lenght ({len(pubkey)} bytes) "
            msg += "for m-of-n multi-sig scriptPubKey"
            raise ValueError(msg)
        scriptPubKey.append(pubkey.hex())

    # FIXME: handle script max length
    # FIXME: enable lexicographic key sorting
    n = len(scriptPubKey)-1
    if n<1 or n>16:
        raise ValueError(f"Invalid n ({n})")
    if m>n:
        raise ValueError(f"Impossible m-of-n ({m}-of-{n})")
    scriptPubKey.append(n)
    scriptPubKey.append('OP_CHECKMULTISIGVERIFY')
    return scriptPubKey


def p2pkh_scriptPubKey(pubkey_h160: Octets) -> List[Token]:
    """Return the p2pkh scriptPubKey of the provided HASH160 pubkey-hash."""
    if isinstance(pubkey_h160, str):  # hex string
        pubkey_h160 = pubkey_h160.strip()
        pubkey_h160 = bytes.fromhex(pubkey_h160)
    if len(pubkey_h160) != 20:
        msg = f"Invalid pubkey-hash lenght ({len(pubkey_h160)} bytes) "
        msg += "for p2pkh scriptPubKey"
        raise ValueError(msg)
    return ['OP_DUP', 'OP_HASH160', pubkey_h160.hex(), 'OP_EQUALVERIFY', 'OP_CHECKSIG']


def p2sh_scriptPubKey(script_h160: Octets) -> List[Token]:
    """Return the p2sh scriptPubKey of the provided HASH160 script-hash."""
    if isinstance(script_h160, str):  # hex string
        script_h160 = script_h160.strip()
        script_h160 = bytes.fromhex(script_h160)
    if len(script_h160) != 20:
        msg = f"Invalid script-hash lenght ({len(script_h160)} bytes) "
        msg += "for p2sh scriptPubKey"
        raise ValueError(msg)
    return ['OP_HASH160', script_h160.hex(), 'OP_EQUAL']


def p2wpkh_scriptPubKey(pubkey_h160: Octets) -> List[Token]:
    """Return the p2wpkh scriptPubKey of the provided HASH160 pubkey-hash.
    
    For P2WPKH, the witness program must be the HASH160 20-byte pubkey-hash;
    the scriptPubkey is the witness version 0 followed by the canonical push
    of the witness program (program lenght + program),
    that is 0x0014{20-byte key-hash}
    """
    if isinstance(pubkey_h160, str):  # hex string
        pubkey_h160 = pubkey_h160.strip()
        pubkey_h160 = bytes.fromhex(pubkey_h160)
    if len(pubkey_h160) != 20:
        msg = f"Invalid witness program lenght ({len(pubkey_h160)} bytes) "
        msg += "for p2wpkh scriptPubKey"
        raise ValueError(msg)
    return [0, pubkey_h160.hex()]


def p2wsh_scriptPubKey(script_h160: Octets) -> List[Token]:
    """Return the p2wsh scriptPubKey of the provided SHA256 script-hash.
    
    For P2WSH, the witness program must be the SHA256 32-byte script-hash;
    the scriptPubkey is the witness version 0 followed by the canonical push
    of the witness program (program lenght + program),
    that is 0x0020{32-byte script-hash}
    """
    if isinstance(script_h160, str):  # hex string
        script_h160 = script_h160.strip()
        script_h160 = bytes.fromhex(script_h160)
    if len(script_h160) != 32:
        msg = f"Invalid witness program lenght ({len(script_h160)} bytes) "
        msg += "for p2wsh scriptPubKey"
        raise ValueError(msg)
    return [0, script_h160.hex()]
