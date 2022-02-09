#!/usr/bin/env python3

# Copyright (C) 2017-2021 The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

"Tests for the `btclib.dh` module."

from hashlib import sha1, sha224, sha256, sha384, sha512

import pytest

from btclib.ecc import dsa
from btclib.ecc.curve import CURVES, mult
from btclib.ecc.dh import ansi_x9_63_kdf, diffie_hellman
from btclib.ecc.sec_point import bytes_from_point
from btclib.exceptions import BTClibValueError


def test_ecdh() -> None:
    ec = CURVES["secp256k1"]
    hf = sha256

    a, A = dsa.gen_keys()  # Alice
    b, B = dsa.gen_keys()  # Bob

    # Alice computes the shared secret using Bob's public key
    shared_secret_a = mult(a, B)

    # Bob computes the shared secret using Alice's public key
    shared_secret_b = mult(b, A)

    assert shared_secret_a == shared_secret_b
    assert shared_secret_a == mult(a * b, ec.G)

    # hash the shared secret to remove weak bits
    shared_secret_field_element = shared_secret_a[0]
    z = shared_secret_field_element.to_bytes(ec.p_size, byteorder="big", signed=False)

    shared_info = b"deadbeef"

    hf_size = hf().digest_size
    for size in (hf_size - 1, hf_size, hf_size + 1):
        shared_key = ansi_x9_63_kdf(z, size, hf, None)
        assert len(shared_key) == size
        assert shared_key == diffie_hellman(a, B, size, None, ec, hf)
        assert shared_key == diffie_hellman(b, A, size, None, ec, hf)
        shared_key = ansi_x9_63_kdf(z, size, hf, shared_info)
        assert len(shared_key) == size
        assert shared_key == diffie_hellman(a, B, size, shared_info, ec, hf)
        assert shared_key == diffie_hellman(b, A, size, shared_info, ec, hf)

    max_size = hf_size * (2**32 - 1)
    size = max_size + 1
    with pytest.raises(BTClibValueError, match="cannot derive a key larger than "):
        ansi_x9_63_kdf(z, size, hf, None)


def test_gec_2() -> None:
    """GEC 2: Test Vectors for SEC 1, section 4.1

    http://read.pudn.com/downloads168/doc/772358/TestVectorsforSEC%201-gec2.pdf
    """

    # 4.1.1
    ec = CURVES["secp160r1"]
    hf = sha1

    # 4.1.2
    dU = 971761939728640320549601132085879836204587084162
    assert dU == 0xAA374FFC3CE144E6B073307972CB6D57B2A4E982
    QU = mult(dU, ec.G, ec)
    assert QU == (
        466448783855397898016055842232266600516272889280,
        1110706324081757720403272427311003102474457754220,
    )
    assert (
        bytes_from_point(QU, ec).hex() == "0251b4496fecc406ed0e75a24a3c03206251419dc0"
    )

    # 4.1.3
    dV = 399525573676508631577122671218044116107572676710
    assert dV == 0x45FB58A92A17AD4B15101C66E74F277E2B460866
    QV = mult(dV, ec.G, ec)
    assert QV == (
        420773078745784176406965940076771545932416607676,
        221937774842090227911893783570676792435918278531,
    )
    assert (
        bytes_from_point(QV, ec).hex() == "0349b41e0e9c0369c2328739d90f63d56707c6e5bc"
    )

    # expected results
    z_exp = 1155982782519895915997745984453282631351432623114
    assert z_exp == 0xCA7C0F8C3FFA87A96E1B74AC8E6AF594347BB40A
    size = 20

    # 4.1.4
    z, _ = mult(dU, QV, ec)  # x coordinate only
    assert z == z_exp
    keyingdata = ansi_x9_63_kdf(
        z.to_bytes(ec.p_size, byteorder="big", signed=False), size, hf, None
    )
    assert keyingdata.hex() == "744ab703f5bc082e59185f6d049d2d367db245c2"

    # 4.1.5
    z, _ = mult(dV, QU, ec)  # x coordinate only
    assert z == z_exp
    keyingdata = ansi_x9_63_kdf(
        z.to_bytes(ec.p_size, byteorder="big", signed=False), size, hf, None
    )
    assert keyingdata.hex() == "744ab703f5bc082e59185f6d049d2d367db245c2"


def test_capv() -> None:
    """Component testing of the Cryptographic Algorithm Validation Program.

    https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/component-testing
    https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Algorithm-Validation-Program/documents/components/800-135testvectors/ansx963_2001.zip
    """

    # fmt: off
    test_vectors = [
        (sha1, 128, "1c7d7b5f0597b03d06a018466ed1a93e30ed4b04dc64ccdd", None, "bf71dffd8f4d99223936beb46fee8ccc"),
        (sha1, 128, "5ed096510e3fcf782ceea98e9737993e2b21370f6cda2ab1", None, "ec3e224446bfd7b3be1df404104af953"),
        (sha1, 128, "9fb06aa8dd20e947c9216359630e588b6cd522dd71865ab0", None, "a1f9cef361c26fb9280f582851ecd5f2"),
        (sha1, 128, "613411bedfba26cbddec4fd68c3ae2c40a2255ae0f5c46ee", None, "d8106c1ee5e7be18fa2e3550459e24f7"),
        (sha1, 128, "445776ec51f2c9aae125dd6d6832210eee69249c4c7ad2db", None, "96f1cac19f41a8ce5f5bdd84856b89ba"),
        (sha1, 128, "1c3a4b420de31f5092e0568847d8ba9f84376ccfe5224c19", None, "5c2e39b7571111ba6cad54b63abd3536"),
        (sha1, 128, "0147fee06dd9918cd1654132227313b104bf99b1ad1f1c46", None, "098758b7ed8dac02a5991411b76b3d2c"),
        (sha1, 128, "50ee47d625dcb6a6196c148d452e99bb0a1cf1fa82cdc3a9", None, "9e2a45a4a8984a563f5776ee7ebfd5c6"),
        (sha1, 128, "ea2c79dc2ef00afa448cb8d390998d5a18f27f5d888e472c", None, "c5d126d15ca3d358ee78db4c1ba0df44"),
        (sha1, 128, "424d414d4b63c7cafe05d4d8bf8b6ce4438eb329a650354f", None, "a5370056ae13f6270490ded98b08c68b"),

        (sha1, 1024, "fd17198b89ab39c4ab5d7cca363b82f9fd7e23c3984dc8a2", "856a53f3e36a26bbc5792879f307cce2", "6e5fad865cb4a51c95209b16df0cc490bc2c9064405c5bccd4ee4832a531fbe7f10cb79e2eab6ab1149fbd5a23cfdabc41242269c9df22f628c4424333855b64e95e2d4fb8469c669f17176c07d103376b10b384ec5763d8b8c610409f19aca8eb31f9d85cc61a8d6d4a03d03e5a506b78d6847e93d295ee548c65afedd2efec"),
        (sha1, 1024, "6e1373b2dd31b74b638e86988eb9e918d0c96f46cd5b3a92", "19743dfab297303399c4197c4346ee3a", "57ef215679ca589af756ad2208761fd26fc828da6ebb28bfdd9bc8028d264b3a5c6f6d2dd3de7e1d914e99cb6522e233c26d9ab51e3d27ff532785889a553e44538a085b900cb9209849350df7183e3b0ba73077e42b9c5a769b843e25ef507b9c5ed88d54302e71e16f986a1b20d93948d61f208eff1741e5b7aa490734bde8"),
        (sha1, 1024, "b195b8c3c7bb7ceba50ea27c3c2e364559e1fe3578aa715e", "d5b35fd5f49cc116c019029b08c85ef1", "ba02df6edf41d941703e407572820310eb9db401d71c91f392bc18039e2fb5b250df267f3cdc244313b6c016f247e65cf3006270806495189e97015bbb0b3774b9b147303be32c41b8878ca57a6a4768675688a61ec859e3d4bcef4c5ec97eb654591879c85207a21f5dac6f51e1133bcb08c518817fd6c249011e44af678b50"),
        (sha1, 1024, "6858a77d2b9db2281238103faf6829bfcb631b9d936b127a", "332a4693ddf068f331b1cf9db9ef6a73", "e1ce87a741be93af506bd2a49a8b88cabd5f7ab370de3a0d943d5a10b3deb4088bf7f26d863915cb9d5cbf491c816a570bb021adb7348355b942d6551e8f783475d4f448514f92190d380bf31535eb1af49779eed6f2ffe7f6aee4e0095e8e7a3505cad3ca531b12d51cb5ee742cb46fddcb0740c8ef7e9c208b38f780f98e3c"),
        (sha1, 1024, "c94d3dac0f574192b54e254c211336eec808bd84caf986a8", "8f6d41388cc7f75da870ed81caa645dc", "4b6ba78ed72a11eac83048df87caa92ebcb0ea0f3d4ed3124c6193e806d2cb12862a0dab34c0b1ebe873526dd9c354ed0491f71b00f425988e74276f288f966d7bc12dd6346fa073137dc03365591642c876c93b870e0df8cfecac587a6e8718f980aa8d625e4183dadaba8990e958a0849bbd6a7524fb7e6f7ae0963284ae71"),
        (sha1, 1024, "6abda986108e8a5134057f679850dcf088ea3c43658996ab", "a5bb20b7e8196838e40239b08737f481", "8e2bf5df0c82175e165745ce45808e0006665c0bc44a46b9ece98d2335a06aeaadbc0194437529303627d01488793f9797b343a2c20114715e5fdbfe04b58190d9721857aa00524ec817dc9f479142906119f72e05a6bc01e6c17b74f5ce597de61400939d640aea23831531e42e6d92fbf0b29e4ce6b9656e59d2356dc54a50"),
        (sha1, 1024, "74c1ff417476636d3fa4ee48f5eab876d661d67128348db6", "4f34bd9a38b57dba2b5a4e97c99eb4c2", "65f81d448eaa84c53a3261d4a8894ee38c7b1cdbe8f0118fe9140093323795fd8bdde40ae27d18dfe37207b295d70e0c92dc9e63980f2b3ec0ecd6a5e908aa319dbb0ca1a9e275d32a479f86e6ab3102c380efec1d22ab4c6e21b045ef7ed75b35e7b357065857deec39580850b3881645bf42a3d903fb9ede4c04a6887c382e"),
        (sha1, 1024, "a655d8b0f737061eaa5a692dcc1c92a19b3103c876ccab31", "e7796de6ae29ce6f8e1f4eb8a81d1727", "583918aa2f85ccb17c624266afae509909a9be9121453a526aaf6cc87f903122dcdc14bafde13e2b878f270e1f86f569ab15e12a227c843d361fd8230e465453d5f3b5fb32b3175ba2e8e4aa473c3792f57485f6b022bece57651f7bbe95f1bfb9d7bb9ce712eb30233972dfb6258620822e496305bef740115312e808db039a"),
        (sha1, 1024, "3f6d287da6237895c4ed10dd5c4fbb5fe08eaac5bb314c7b", "0151cb9a7944494ce88eed12b05a3aaf", "d52041563204a69dc1f6f72d9b12e40d4efa35be050b2a677ae43717fa51ab21c75f9853fc701d9270ed2e8e493e15453cc98c0cb7ab07b3b23aa9e241eb3dcc8e401328e86df4c5b83256738782605271f52b17434eff72a1a3b4f45c4a52bb493f9cfd0e9bfd8decd86ce844c0888221abbc08e827cbbba12618ca39f54f1c"),
        (sha1, 1024, "9a71e94ab0b17f0b219fa95ac061d553a4639e89539b023b", "e274ffac839cf3c16266c058627e63fc", "974c1ca2ed816208862029ade68cee9a2877e3e6c7f320dfe6336c3d5ebf57d4fbd40766fe42cca6a91f7092542857560de5fec7813e79e0412fa773adb3a4e43fc13b7e899a6c5acad0848d6156087d0431509dadb55469cac922565bca451505c4f18fe97f9ab71016fc4e641d016bcba34aa6ae7c1e3acfe08b5fd95aa484"),

        (sha224, 128, "9ba3226ba0fca6bd5ddaef5b8d763a4d3303bc258d90468c", None, "15ccbd7d6b8f918335799b3920e69c1f"),
        (sha224, 128, "fc87aaa2d23ebabdb912c153d3a675da556a57df0699e479", None, "e22c69198766563bf0cbc07628eff5f7"),
        (sha224, 128, "f557b1ba1162cdc06cd531d5376a6575cad3e3b0f1508cc0", None, "35183315fba3ffb68a97b1eb5c052021"),
        (sha224, 128, "daa88161947e99d50e0400a79fa70b13e0d0a578f38d7fa0", None, "c76ea452168ae2ae6f4b78c695e2ac76"),
        (sha224, 128, "30b694d1454a10bdd5993da1a5c466e0821bf426ad7b8b40", None, "bafc2a0a75b9bfbdf1356a60a7937aa8"),
        (sha224, 128, "79bf9d93badd5a3eff9ab4c30c44b1985f5e7266e246e777", None, "f3a3c2ed92eebdc35b403843fdb8cd97"),
        (sha224, 128, "79496976705d6edea6fe1d7113263ce1eff221020c89db0b", None, "27cb9631cbb1b4f86aee8c2cf1718be0"),
        (sha224, 128, "2adc3b158cb63d7afa417c5d832b01bfc0aa34ceb35411ca", None, "e648b78032930639e5c210d798203f98"),
        (sha224, 128, "c8ae013dbfa53e9806d21b4deb7e761dbc515f2249afcdb2", None, "44c96abaca4ac9373b58c5af34880dbc"),
        (sha224, 128, "9f562ec0869dce142d378909b3610b02108b158719b573f9", None, "252c6dcaf650d92c09c8dae4dc0934cf"),

        (sha224, 1024, "da67a73072d521a8272c69023573012ddf9b46bff65b3900", "727997aed53e78f74b1d66743a4ea4d2", "dfc3126c5eebf9a58d89730e8d8ff7cc772592f28c10b349b437d9d068698a22e532eae975dfaf9c5c6a9f2935eafb05353013c253444e61f07bc9ddd15948e614bdc7e445ba3b1893f42f87f18fb352d49956009a642c362d45410b43a9ab376e9261210739174759511d1f9e52f6ec73dfed446dbafaf7fd1a57113abc2e8d"),
        (sha224, 1024, "0aab8fffc75e03810fefe1d1f170e8fb860d3880b2206944", "d318ac8eb3c51d8e8e88b8297f79ff26", "9bb6698705db9646ed360a8247396efc92c3450bfaa177c07459dfa8cc108cc8eb98c1e92e8257443463f531c01518fe8d4355784a7df2eaef16908d91104fdc917950b3816146f24a6845a5adad248dda41fcf611954f4de41f357c48f48910a48a1f26b9eff1434b9138848d4b03f05ab6d928c6b9a1b9ba8081405ec45c5f"),
        (sha224, 1024, "ccd2f983a0462b12762392bb02f66ffc44da3155111518f6", "9f90a5a197f316275e4376c262f83345", "9b2c47c1edb54b01e6f26236299262270bb82b3de85f744756c1d811f5db1c95dae1484cfab9119b0f75161efbf3a8a69b5f663b7b484bea7009c53e020e8aa009fe8616de2c932bd41d3d2783ee488c024eda2806f0ef324d16a9a95370c5d9ea277fba8a9d23a2a3051524bccbdcabb62e3550170900da7cf403736fb41823"),
        (sha224, 1024, "384f91ff8495828524e558fbb5acbd1e8b0ac597d8dd8efa", "a389ee5959381ab6a7240ab3322a2c8b", "3ef814c4724372a48b05c6d2cdddef4b57c2cce711860429ab14d87df79a5ee97fbcc8db83f6bc8ad08deceb3e4c09a87691bdffe79791edb409d3af1121750acb9b4a35f76cfb96a707faf4c5a3a455f80637e162202a55d10ac977cea4e62df1536493c6e51f40f7ed76bc38071e192d33018381fcfe8655fe2d82f2052208"),
        (sha224, 1024, "0fea3ff05fdc02af194a4502c4f8968ea696589666e3e5a1", "8f1736597687a0e50f9795f5ce4a794b", "3276318049fb0f809e3eb919e628dde6c8a661147d68a843a0217d49066711652a77956a86eec57d56d62dd9f41149d815fa46416157a6793cc2e0bbaf7de75b78fd532e296064525406781229e6cf657bcfedb110fb6889d9c5d0fce5ae5d9129941f238db5f6de160b15d11bb01b42498a79c8b714ece7a6c50fc5919da383"),
        (sha224, 1024, "c425bb77c93b59bade4f0fade4f58a61ac3540a186b806ce", "46a7e50d6e084eaf34f997edd0e71324", "603cbf3606c22368c7dcb03c0ff22f94c4e7190af58715e8a630d48dd48acbb2eb72ad2e596c1373dcfd76b36e24461a3c6eb70d5a13217db5fa706fe7cb0004d6eb6b41ef87964262f3f71f588c1506e575051490c78cf1c87c495a31049b42f165cd468c2de294d840ee79f0d8a27ba5985fa37eddc14ccce7ed56a1cc73fb"),
        (sha224, 1024, "f5e674ecf26fcb110cbf6617ca81645552c95787e42b59b8", "791c6a02432eeb4e9e09d1666d80edb5", "e03f4a184cfd06361b87eecfa8277ed3bd5d176bb6a1ed7fbe0f1cb7432f394cbf3ec94bd64c275f2dd40531693c2d8c82c4f57057c29d6ca38551490ec66ad7f650a3aa7528fa3bfcb6dd5455cf2158254b7d3284cb91e2154d0042af7b38fb58268196865bdcac6326ef3ae4fa2a38f4844c716518506b6cd2b032681dc851"),
        (sha224, 1024, "e5036244d705de12354c712df9e9b45282fd7969b479601b", "2fd1ad5b6b5a6606ca8bbe1fdf651b37", "f7b412e63aa9fab0435f64ab9f5a6c90d924bf2057ecb311529ed761f7ef939bd765d38e9eadbc8d16667ac3751c3111a932f815bb00af80a78139a05b3ecf3c7074f4b17e81188b49c91b9bf681066d0a6c62561489f1b660a6a9626b23355cbe189bf4a7cf8667608b582dced3ce883b9cef9b2e01667b2e894d80599d2555"),
        (sha224, 1024, "34a8b50ddfe5643d8eb284cf817074955fe85251cc40c116", "79b1b79134f4bc2247bab4d401441f66", "69bea882176d4475bd68f6b040482da6c5287be9e9a773e1a4c70c7dcc16fec975b05c589886d0f67f69103a668c4f23908b9261b6cf81b6ebf2c24693e32d2814483a471a8e70e33e9c1fef5d1714fc1a2a55a22b9ea14868eff726da3c113dce79df3413129dfca11e331df57cc127094eff6b41b8e6e92b5bc7a8ad6679a1"),
        (sha224, 1024, "295bebb724f5bd120c97690d034487e60398fbed6facca88", "1a45c3460cf33d23209aa90a3c4ca708", "e72d4748fbc36b163efe655d19a0aca946baf35cbbfe4c9a69b81597348c53740fda2ece02baa6f7a9f2b64195c09840e4c2d1e11a229243e3014c7cfcbca5afb1a209af6955b3ef1234f1c45ad458bcfa458041eceff639756a2d81a2bfa64687df82a791f96f9441e9f72b5a11c4246acdb75f176c5a89bec7ad36da651f5c"),

        (sha256, 128, "96c05619d56c328ab95fe84b18264b08725b85e33fd34f08", None, "443024c3dae66b95e6f5670601558f71"),
        (sha256, 128, "96f600b73ad6ac5629577eced51743dd2c24c21b1ac83ee4", None, "b6295162a7804f5667ba9070f82fa522"),
        (sha256, 128, "de4ec3f6b2e9b7b5b6160acd5363c1b1f250e17ee731dbd6", None, "c8df626d5caaabf8a1b2a3f9061d2420"),
        (sha256, 128, "d38bdbe5c4fc164cdd967f63c04fe07b60cde881c246438c", None, "5e674db971bac20a80bad0d4514dc484"),
        (sha256, 128, "693937e6e8e89606df311048a59c4ab83e62c56d692e05ce", None, "5c3016128b7ee53a4d3b14c344b4db09"),
        (sha256, 128, "be91c4f176b067f465244742a9df72ca921a6acf462739a4", None, "41476c80696df4e87fb83e55524b89ce"),
        (sha256, 128, "1d5b0ad85bc7859ada93dd5ccaf9536761f3c1a49a42f642", None, "650192990bfcaf7366f536aa89f27dbc"),
        (sha256, 128, "265c33d66b341c3f5ae2497a4eff1bed1cd3e549095bb32a", None, "0066528a1bd57cd92bd619e60b605f1e"),
        (sha256, 128, "03213ad997fdd6921c9ffb440db597a5d867d9d232dd2e99", None, "5a00bd1c812c579507314b491e4e1dfc"),
        (sha256, 128, "3ede6083cd256016f820b69ea0dcd09f57cdab011a80bb6e", None, "026454370775578e3b4a3e09e97a67d2"),

        (sha256, 1024, "22518b10e70f2a3f243810ae3254139efbee04aa57c7af7d", "75eef81aa3041e33b80971203d2c0c52", "c498af77161cc59f2962b9a713e2b215152d139766ce34a776df11866a69bf2e52a13d9c7c6fc878c50c5ea0bc7b00e0da2447cfd874f6cf92f30d0097111485500c90c3af8b487872d04685d14c8d1dc8d7fa08beb0ce0ababc11f0bd496269142d43525a78e5bc79a17f59676a5706dc54d54d4d1f0bd7e386128ec26afc21"),
        (sha256, 1024, "7e335afa4b31d772c0635c7b0e06f26fcd781df947d2990a", "d65a4812733f8cdbcdfb4b2f4c191d87", "c0bd9e38a8f9de14c2acd35b2f3410c6988cf02400543631e0d6a4c1d030365acbf398115e51aaddebdc9590664210f9aa9fed770d4c57edeafa0b8c14f93300865251218c262d63dadc47dfa0e0284826793985137e0a544ec80abf2fdf5ab90bdaea66204012efe34971dc431d625cd9a329b8217cc8fd0d9f02b13f2f6b0b"),
        (sha256, 1024, "f148942fe6acdcd55d9196f9115b78f068da9b163a380fcf", "6d2748de2b48bb21fd9d1be67c0c68af", "6f61dcc517aa6a563dcadeabe1741637d9a6b093b68f19eb4311e0e7cc5ce704274331526ad3e3e0c8172ff2d92f7f07463bb4043e459ad4ed9ddffb9cc8690536b07379ba4aa8204ca25ec68c0d3639362fddf6648bcd2ce9334f091bd0167b7d38c771f632596599ef61ae0a93131b76c80d34e4926d26659ed57db7ba7555"),
        (sha256, 1024, "fd4413d60953a7f9358492046109f61253ceef3c0e362ba0", "824d7da4bc94b95259326160bf9c73a4", "1825f49839ae8238c8c51fdd19dddc46d309288545e56e29e31712fd19e91e5a3aeee277085acd7c055eb50ab028bbb9218477aeb58a5e0a130433b2124a5c3098a77434a873b43bd0fec8297057ece049430d37f8f0daa222e15287e0796434e7cf32293c14fc3a92c55a1c842b4c857dd918819c7635482225fe91a3751eba"),
        (sha256, 1024, "f365fe5360336c30a0b865785e3162d05d834596bb4034d0", "0530781d7d765d0d9a82b154eec78c3c", "92227b24b58da94b2803f6e7d0a8aab27e7c90a5e09afaecf136c3bab618104a694820178870c10b2933771aab6dedc893688122fffc5378f0eb178ed03bac4bfd3d7999f97c39aed64eeadb6801206b0f75cbd70ef96ae8f7c69b4947c1808ffc9ca589047803038d6310006924b934e8f3c1a15a59d99755a9a4e528daa201"),
        (sha256, 1024, "65989811f490718caa70d9bdca753f6c5bd44e4d7b7a0c98", "264a09349830c51726ca8918ae079e4a", "f5f6ef377871830807c741560a955542dcedb662784c3e87fba06bff83db0d9753b92a540e5c86acfe4a80e7657109ee3178879748d967635a0122dbf37d3158c2d214c3dcba8cc29d6292250f51a3b698280744f81040275e9a8b6ee5c9b0307db176364868deade3becc0711c1fb9028c79abad086459c3843f804db928c49"),
        (sha256, 1024, "9d598818649fc81b8c59f60dfd41784790c971eefcff6419", "435f06ac33386eaf3af9042d70b93b08", "970845c707dafb8699fa26b9f6c181f358ebed337f9504b04b515c9f01db12dd4965e65e8750af575c0934527183ccbe8e243f26398906089c11bc8a8f69bedbbcf651c19c219b5bd0dc1829931cc6994d71f0000b7e42b1b994aa332b4a0bc506cde8723cd8da879826c585ae12fafb3f3daf5784007006878f4ebc4eda7db2"),
        (sha256, 1024, "4f9c0a5c03c8c3a23f06847d0e1f86f7df8da47bf3ccde99", "45672212c5af77d7eb5c90c38e125b52", "80fd7658118370a7d790d708ddafe6e7a5ba22caaacbf46e73fce6d6e1516a465d8264b75b5286067ac57863949aae984dc00653bf151930b398d7f5478c7b954565c584c8ad36fe59692781f2398d71e0234cff09d3c175d86a6c7c0f1e387eda55da8300caee4173ad7ff74b2effd723defc20060fa69f92b8af858a87a4f7"),
        (sha256, 1024, "1980d2966d59ccbbf89f7fe9a5943da886f232ac02ee69ce", "c8af6665439efbbee8660701681d54ce", "2120434e863d1df7b9748a3cbc73d2680ede19437a13230a9dc4ef692feb5197afd4e9275d6ed00e1ff3a0fd026dc8a2adefc90bf0e8656912849094d7a515bf45dda69e574bf33211255dd78bfc2b83434f1e0f7795d468dd09c4ed88b691b3fb9ce876161b2f26b41614ff05228b3402f0d1f3044c2c3f9f7136c7aca53356"),
        (sha256, 1024, "0eaabe1f7ab668ccf171547d8d08f6f2e06bc5e5f32d521c", "e4e98a7d346906518305de3798959070", "b90a0069ad42b964e96d392e0f13c39e43203371b1eba48f7c41fbfd83df7505d564ce4bf0cf8d956d2a1e9aee6308471d22f70aedd19b24566974f54db2849a79528c9e3f5d4f93c2f6f0862311fca14a2df91635d112fbb05dcd7c0ee72a6d8e713216bc8777596244f724e4046ba134f9a811f8f504ee67b1683041690921"),

        (sha384, 128, "d8554db1b392cd55c3fe957bed76af09c13ac2a9392f88f6", None, "671a46aada145162f8ddf1ca586a1cda"),
        (sha384, 128, "070265bd04222fc1dcb67182fa797166eaa18a2a1e1a6c0f", None, "522d79f65430350cec5c59c014e1a2cd"),
        (sha384, 128, "4e7ef0743a0a14fe21eaa9cbcec68581e75a616c76814c61", None, "4ac7317e0f82ff9256f1584a24661446"),
        (sha384, 128, "8952079916141dca1ce53d0d221269db0130f99270129ea3", None, "5910e2945753e0d0a0d60afd54815a3b"),
        (sha384, 128, "646e92b7bf5e747bb7ba5afbe6d2028bb93147be73fcec60", None, "ec2c0633e51c78880bee00e63d40d103"),
        (sha384, 128, "cd09e15099aec9baa47bb343d156afe8e0cd33f8dbf104be", None, "f72c76cc83bf273c7e5129d1706e3330"),
        (sha384, 128, "bfd00866e7a7e147fd98e1defed9fa1ab32d3e785a3f3436", None, "10c4874e47a1032cb9307dd4b4cad9f9"),
        (sha384, 128, "f07d1c1d8d3435c9477303c87ae19a0b8acf890c11b19794", None, "ecc66ccf0bcfaa644787203178647091"),
        (sha384, 128, "eeb2e06aad13b543746a9e5411066d4ef5717bc753eee1a0", None, "2d750acfa410f23e6993747536aaee9e"),
        (sha384, 128, "ba3ef5d54aadb1824dd974edf1748d76b7b13d26e83fa9f9", None, "55182a2abb9dc1d79d64b09c4c4666ee"),

        (sha384, 1024, "c051fd22539c9de791d6c43a854b8f80a6bf70190050854a", "1317504aa34759bb4c931e3b78201945", "cf6a84434734ac6949e1d7976743277be789906908ad3ca3a8923da7f476abbeb574306d7243031a85566914bfd247d2519c479953d9d55b6b831e56260806c39af21b74e3ecf470e3bd8332791c8a23c13352514fdef00c2d1a408ba31b2d3f9fdcb373895484649a645d1845eec91b5bfdc5ad28c7824984482002dd4a8677"),
        (sha384, 1024, "2c9436cd85df982911df60d54f2d41d81660cdb37e457daf", "6b5910575296437a75c04371c8623cf6", "6efb45067e00024beaa9fa763ef2c701527cd9eb5697f7f77475f2d36495058e3558893006ab0169e9a9f78481f6f06e9b005413856af89cd764beba0fff6ed4a077ffd36f966b633e058793320febf52b937554539096838873171933c2b7f864000be1b3a01ad6c4e66c3190bbfc90d7deb31e8857cf272cdd2caea730839e"),
        (sha384, 1024, "04bac3eccc8730c441c12f050168643c3581c046067eb930", "6f75d4e7ec627f047589c588d20a8ae0", "64be249badec07779df8c40e3a75ebe7296f4c853e8c596d208f6c9cc7b41b75db28aa31a9199eabb750c28804739cbdabf81f2b9579c0e0bb3dbab77a0315ce1f7d4cad83e2cbd4258f132f3ccbe522da73ba0b389b6963d227c3aa61dbdde64517cd05599596dd9e73b85e0deede8a822821b4a27403116919f40f75cc7c42"),
        (sha384, 1024, "684ac84d726909080f8d6bd89d8a744ced207c5bdb4bf866", "ae59a73e8b3c3b59f01fec8e7efadef9", "e312c7c168c69e3c0e0894c7a4b561cf8e38c3dfcbc90c8934edb8b16f7031cf595a093d6289a01fd977c0bf216c04edaa21230e82bd0f066a60180174df85482dd6353111da24bf979422e3fb7b34720310075abba72c5f0ac6bfd7c6af331532ce7b1d3b9628ab4502614f9e324177ad33f7257a4c1efcecefb83f446242e1"),
        (sha384, 1024, "74a215aa43a7f59fac674d220c852e91a30e7ad05b1b7223", "8bd8cc5c429502d5ed0da3fe706a52d4", "3d836e700d223a088647eb9a323f7b7b19ad071818141182e216cd9644396b01d6b3d3e1fc2cefa2794bf7d9d27f10b0716ae3ec100e171cb6188c5a23da1b7500879b014b4878455b17f049060cb46c57c1b0670eb8cfa3b478ca0501ed5c258773b862f0eadb0991eb56a4f51aadb1287179bd7a366ac16c235d7b11d96048"),
        (sha384, 1024, "5318d9e0ec5d6f82bae244f01e3e5281e954b924d1554fee", "c0537c7929f6efe8399c8089552214a9", "38083a961d8967e11096a99d36c198b3527dfbda74c2f4e9cfc7b5a115333d2be242b192df027ba4c1f732f1c26ae94b8cd3fa2ecd59df9be5baed7c479da001798a4a623ae01fe1b1feb83f436fc4b3268bd56b17579c0d7ad0df9296db3f57f26a7de0d64b04311c81d70fdec19cd8acf0e5a03b60059172475b104aaf92cb"),
        (sha384, 1024, "d427c25cc0d5c499aa789cbd9a0f2a358596e0a586d6aaad", "b0db1a8f05b1ed0ac6594f882d61da82", "f800e7ed9cf7a632ceeda04ea75f6fd7efddcd96cf6ec03052cb4c71f52a61ea96d363f1d07704fe51765135624a55b64cefe6c7f7e653d6a404911a99ecd6f437a9e770b6c60601d6001165b37e6005548f454493429dce77ac3311f817a88f8b14a4a2bab4b2cb142f5154c9a23bf6818bcafad4b8d0fe50c1392b12196a62"),
        (sha384, 1024, "fff1206cd5e2aff982c47d5dd31c2ce50e6718f4d2126427", "74b3285de80d0c1962b6c9c6dc9cd5bf", "d8b2cc9655a2cfa338e76cdf17258501b69a04057947c4083fd76bdfd73d48a6cb9e8538317bff5e829e006661e0ab53a9dd5ff210c8b59ff6ae64220bcab7c84facd792583c34177a867c69e117688bec10d134c003f112ca600eb6c514df0be5daa73bc9b4800403f79424ff3313b95d009ff423655774487cc1465731936b"),
        (sha384, 1024, "75a43f6464c2954efd9558d2d9c76cfcafefec3f07fe14af", "6744c4a41d5bd7f4ca94ea488605c3d3", "5045a6252c9b6eb80debc67e0d11a028bf8e1f0b274d13aebcc7d565e1b73ed228c5f4195ebd1044aaf9a755c6945a729767f8f3697adb2941df0f449fdfca8f84abefc5011d4b968ad1f79b535bf124e3dcf131f8f894ee633a040c34a6470544497ae3d96c1e4bcdc5914d40c4a73f1e174b29bd5755d1aa0a3ddd3f9428d5"),
        (sha384, 1024, "09807be0ca8c534a0e2b326a845054a5389c85a1d60f84a5", "43b0be9359d0bbecb75958d566decdd3", "a00e22994f134f1a0da919fa43a779314c5e706ab3fa4c1d72912cf1109b958a141075d206a7befe467efa85ab2d1a83d1a438bda7df009e1eaf66649920d9dfb4110a36575f034ad0a63344968dc0e171ea2972fda011f66e8bda6867eb769281af23488b5166c85289ad3a68407010ae6f62227a1c1d19a6f527c735dc145d"),

        (sha512, 128, "87fc0d8c4477485bb574f5fcea264b30885dc8d90ad82782", None, "947665fbb9152153ef460238506a0245"),
        (sha512, 128, "293e901c8f43178794a9792f98861732faa4677e72b8ce1e", None, "883e84f877b05a092ada456571c58cb9"),
        (sha512, 128, "734315a823c278adb4517c952b0ae3f6fe2de6615b1c2650", None, "c8ee447ad8e7ff0a874e89b11616a824"),
        (sha512, 128, "fece4214eb02a10d11dd7dffb0bd884e4aedbf705fa3726f", None, "2491f93f072adca1c051d800b5d82dec"),
        (sha512, 128, "4ee79bcb0d621a7a0d42cd9a496b209dfd3f4276455139e0", None, "bdb3e1cf4414b0ba1829810defc94024"),
        (sha512, 128, "18447afe05107a7729661bd1b23935b30983ff614631dec8", None, "1d1c68eabdfcfdd62a42d43a3e98c772"),
        (sha512, 128, "c32dffc642ae400dfc21ade6adb936583999d5cf1379b783", None, "8a1abd901b090f808b2f1e355c6eb596"),
        (sha512, 128, "57d4d684aa3543d6097bc7c0d0430527e1937b0f936ab479", None, "33f781afd506a4206b9b3af2371a67a4"),
        (sha512, 128, "b7d969a749af87a02c0629c642bfc5e2e2aa10d015fde9ca", None, "dfbf12c462bc114997317b13c9cdda65"),
        (sha512, 128, "fb03ba6b357d26ee18a22bdab14da74ca5727ed4b69a687b", None, "8dcdf450dd810e20c472d485a78a2d5f"),

        (sha512, 1024, "00aa5bb79b33e389fa58ceadc047197f14e73712f452caa9fc4c9adb369348b81507392f1a86ddfdb7c4ff8231c4bd0f44e44a1b55b1404747a9e2e753f55ef05a2d", "e3b5b4c1b0d5cf1d2b3a2f9937895d31", "4463f869f3cc18769b52264b0112b5858f7ad32a5a2d96d8cffabf7fa733633d6e4dd2a599acceb3ea54a6217ce0b50eef4f6b40a5c30250a5a8eeee208002267089dbf351f3f5022aa9638bf1ee419dea9c4ff745a25ac27bda33ca08bd56dd1a59b4106cf2dbbc0ab2aa8e2efa7b17902d34276951ceccab87f9661c3e8816"),
        (sha512, 1024, "009dcd6ba5c8c803ca21f9996ca5dd86047d4ddc150fddace1b1ebe996c2007e3ee907c8ff03b9ef766e8ceb4dedf7489e5162e2278c0185e4be381bec17dd992cf8", "1e60e51c11a538b0ea8990d69a4c6358", "4e55036a32f32fc965046fdfbf686c108e43a69f8fc1a64ff1bd77763f2eedc8bf277d78b4ce31243e1adbe2c2d5dd59b47503b5b90b54f9d7a9a5aea49c7f0283cb64c3849a1d157000fd41ef6c1d1a5b62734e7c9a20dcfb57f2da974933f57ee619d72898d0e93d9a4254aaddf73941d6269298b4d49c0ac64a33802fe8f2"),
        (sha512, 1024, "01bbc44314f24db4d67a2a7fb5ca3f7a5022790f5875895d448050eda5611a2f39de48e394c5a3df26208eb01f804d0a1d68eece6b6fa96d6db895e133e129094f78", "433e3ee77d00e4a9634efd677e2ff21b", "f1255002293d5fbcf35ad0e532ae872171d11014616a2c52d7e5cb861b0251b9e505a77161c777bafc052b6525a6ecf34590605de72f13a1aff0a61a8a4a3364ebbe2f99224c13e043e497af8a26de749cd257e475b2f0e60e3b594901320a692a4af422f9636e4814b33f67d181a086265013b0d4efd9e1a94ea8a576afde66"),
        (sha512, 1024, "01a33032a2bf6f8e9d6972dd339536c9e248ae9881844ff1bd04af48085be4ca1834f2a94ce1019dd9620d1e3a68203a5b291f40b5f8e3238a2a036312b89061cc60", "d3297ad6b9757d1f5a9d5b0e72176d74", "63565d1d3443620fba4218c97887ff40d6d68bf56b429c22018be5d91c318187ebe8a9399c5cc6c4a849288ab784d4340714ae3fdb426c4a83db9ce2ba8aea80d448e50ad543749b47bcaae519f7f00badd8d48296e81069104dcd293c605b08159ef2ef14c7833739d0414274136ae4db05ba4fa31b29c59de46d9be539525f"),
        (sha512, 1024, "004b20a501776ea54cbdabffec2a664b7a93f8d67b17405a82bd9cbf3685a4659beb2deff1b6ecaa7ab187b6d4fd407f10db6992c65308410deb133be31a0de0c1c9", "fd5462cb37aa298e95f8e34bb49d85ca", "cafcbc117317661bf15277c2881e05e345c1720b0c1c4040c33fe4a3ecf8032802642d29828a077ca91b6fac216b7a06517740c7d633c279dd2115eb7a34fd337376247219f53da32df57070f47c2e0816710080d6492e1c3e8cac818c3cfca2a3ce5cf1515f066b1815d2d2f69fa3111a9e81570963b90a536da0376c12265b"),
        (sha512, 1024, "01fb44335b437771777f14d44e5b634c18c7f570b935228fd3073e3cbde299dfb9f4d64ad720d30e875e8c6bbe181027459c9d3f92a276a38e22faf25f208576a63f", "2359d18657243d61963ceca3fa93587d", "1544e54cd293e533959bdd893337f01ef0c7685a4d8d403d438b0223a7e18330c312a0f16bd819f4359fdd74ae85cc603d35e3d9cba896177452c8dee5214066fca420c3ab522a245af215beb7de52ebb0bdd15d0596b8b763cf7e25610a53efa726b899a1d9727b25ec673ee91ff2111f03cf761a7880d69625e784becfd4e0"),
        (sha512, 1024, "0109afa3904193690d3f2c49e42d08c8c5cd2ea907a0d699c876e418e303b485374c8d6cf5a32af1491b3ea8a3503692b4a0fd78f9b4082e2a6e72345db4532d749f", "7c19631d3cd65915fa4789cf7b1c0979", "fb60175568a66ef4202e110396663085fe2a9d6d2071e55d03c30ea499fee850c99c4e42a7227cca2eaf4d75e37dde205ae07260e84aeee6ef0819d98bd00d0ff5ba55994e7bf2a578baf2ee9aa862d94bf431fa14429010ebc30d7e602de726cdffacaeabc8541237fbc0c975abbf203c018c688ee354d07978654b90de9569"),
        (sha512, 1024, "00632e165775f3c5b6e81d4042f809e904b8167687747638874b39ffce1993f46e8fc44e2a1c3df59563003bad3e25c85b61819e9addc0fdbe173dd4115c38f62ef6", "2bf0f18b7f21c4ec9c20b84c75f66b7c", "c324fed01b75c37fc96703031403d5cc6857dc7ffa48192d9a10d5c69dd6274ecd0eb9a278f9e6b616c27bbf2e3e016635b311940390c52c61a4f4b3383ca6046961dbd2455ff6a982e8269864edd3cc1b1053da7daf9699c61b05f1acca7b79e68db655fd526fdc392bd36dcaf1c5b2fafb8975e318070d4bb948829ac41bb6"),
        (sha512, 1024, "0096172bf47d06d544ae98471490cf9e52ee59ea7a2208b33b26c52d4952bb8f41b2211d3f9ff32e77ca8cc906ba8d246ff266ddf1df8f53824ccb15b8fb39724703", "cf3a74ba86af42f1ae85477ead645583", "995d1ab8557dfeafcb347f8182583fa0ac5e6cb3912393592590989f38a0214f6cf7d6fbe23917b0966c6a870876de2a2c13a45fa7aa1715be137ed332e1ffc204ce4dcce33ece6dec7f3da61fa049780040e44142cc8a1e5121cf56b386f65b7c261a192f05e5fefae4221a602bc51c41ef175dc45fb7eab8642421b4f7e3e7"),
        (sha512, 1024, "0037cd001a0ad87f35ddf58ab355d6144ba2ed0749a7435dab548ba0bfbe723c047e2396b4eef99653412a92c8db74bb5c03063f2eb0525ae87356750ae3676faa86", "eb17da8851c41c7ac6710b1c49f324f8", "829a28b81f9e95b5f306604067499c07d5944ca034ed130d513951f7143e4e162bad8adb2833e53b8235c293cd2a809659ac7f7e392cba6a543660e5d95070c0c9e6a9cdc38123e22da61bb4cbb6ad6d1a58a069e934fc231bd9fe39a24afcbf322ccea385f0418f3b01c1edd6e7124593a1cefe3e48fcd95daaf72cfd973c59"),
    ]
    # fmt: on

    for hf, length, z, shared_info, key_data in test_vectors:
        result = ansi_x9_63_kdf(
            bytes.fromhex(z),
            length // 8,
            hf,
            None if shared_info is None else bytes.fromhex(shared_info),
        )
        assert result == bytes.fromhex(key_data)
