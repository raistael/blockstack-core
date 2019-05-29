#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
    Blockstack
    ~~~~~
    copyright: (c) 2014-2015 by Halfmoon Labs, Inc.
    copyright: (c) 2016 by Blockstack.org

    This file is part of Blockstack

    Blockstack is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Blockstack is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with Blockstack. If not, see <http://www.gnu.org/licenses/>.
""" 

"""
TEST ENV BLOCKSTACK_EPOCH_1_END_BLOCK 682
TEST ENV BLOCKSTACK_EPOCH_2_END_BLOCK 683
TEST ENV BLOCKSTACK_EPOCH_3_END_BLOCK 684
TEST ENV BLOCKSTACK_EPOCH_2_NAMESPACE_LIFETIME_MULTIPLIER 1
TEST ENV BLOCKSTACK_EPOCH_3_NAMESPACE_LIFETIME_MULTIPLIER 1
TEST ENV BLOCKSTACK_EPOCH_3_NAMESPACE_RECEIVE_FEES_PERIOD 6
TEST ENV BLOCKSTACK_EPOCH_4_NAMESPACE_RECEIVE_FEES_PERIOD 6
"""

import testlib 
import json
import blockstack
import virtualchain
import os
import subprocess
import decimal

wallets = [
    testlib.Wallet( "5JesPiN68qt44Hc2nT8qmyZ1JDwHebfoh9KQ52Lazb1m1LaKNj9", 100000000000 ),
    testlib.Wallet( "5KHqsiU9qa77frZb6hQy9ocV7Sus9RWJcQGYYBJJBb2Efj1o77e", 100000000000 )
]

consensus = "17ac43c1d8549c3181b200f1bf97eb7d"

def convert_funds_to_segwit(payment_key, tx_fee):
    # convert payment key to bech32
    addr = virtualchain.address_reencode(virtualchain.get_privkey_address(payment_key))
    pubk = virtualchain.lib.ecdsalib.ecdsa_private_key(payment_key, compressed=True).public_key().to_hex()
    addrhash = virtualchain.lib.hashing.bin_hash160(pubk.decode('hex')).encode('hex')
    segwit_addr = virtualchain.segwit_addr_encode(addrhash.decode('hex'), hrp='bcrt')
    
    # fund the segwit address, and then use the same payment key to send the transaction 
    fund_inputs = testlib.get_utxos(addr)
    fund_outputs = [
        {"script": '0014' + addrhash,
         "value": sum(inp['value'] for inp in fund_inputs) - tx_fee},
    ]
    fund_prev_outputs = [{'out_script': inp['out_script'], 'value': inp['value']} for inp in fund_inputs]
    fund_serialized_tx = testlib.serialize_tx(fund_inputs, fund_outputs)
    fund_signed_tx = virtualchain.tx_sign_all_unsigned_inputs(payment_key, fund_prev_outputs, fund_serialized_tx)

    print fund_signed_tx

    res = testlib.broadcast_transaction(fund_signed_tx)
    assert 'error' not in res, res

    res.update({
        'utxos': fund_outputs
    })
    return res


def send_as_segwit_bech32(txhex, payment_key):
    print 'txhex: {}'.format(txhex)

    # get op-return data
    tx = virtualchain.btc_tx_deserialize(txhex)
    payload = tx['outs'][0]['script']
    
    print json.dumps(tx, indent=4, sort_keys=True)

    # convert payment key to bech32
    addr = virtualchain.address_reencode(virtualchain.get_privkey_address(payment_key))
    pubk = virtualchain.lib.ecdsalib.ecdsa_private_key(payment_key, compressed=True).public_key().to_hex()
    addrhash = virtualchain.lib.hashing.bin_hash160(pubk.decode('hex')).encode('hex')
    segwit_addr = virtualchain.segwit_addr_encode(addrhash.decode('hex'), hrp='bcrt')
    
    print 'privk = {}'.format(payment_key)
    print 'pubk = {}'.format(pubk)
    print 'addr = {}'.format(addr)
    print 'segwit addr = {}'.format(segwit_addr)
    print 'script = 00{}'.format(addrhash)

    tx_fee = 5500
    res = convert_funds_to_segwit(payment_key, tx_fee)
    fund_outputs = res['utxos']
    fund_txid = res['tx_hash']

    new_tx = {
        'locktime': 0,
        'version': 2,
        'ins': [
            {'outpoint': {'hash': fund_txid, 'index': 0},
             'script': '',
             'witness_script': '',
             'sequence': 4294967295},
        ],
        'outs': [
            {'script': tx['outs'][0]['script'],
             'value': tx['outs'][0]['value']},
            {'script': '0014' + addrhash,
             'value': fund_outputs[0]['value'] - tx_fee * 2},
            {'script': tx['outs'][2]['script'],
             'value': tx['outs'][2]['value']}
        ]
    }

    unsigned_txhex = virtualchain.btc_tx_serialize(new_tx)
    print 'unsigned: {}'.format(unsigned_txhex)

    pk_segwit = virtualchain.make_segwit_info(payment_key)
    print json.dumps(pk_segwit, indent=4, sort_keys=True)

    signed_txhex = virtualchain.tx_sign_input(unsigned_txhex, 0, fund_outputs[0]['script'], fund_outputs[0]['value'], pk_segwit, segwit=True, scriptsig_type='p2wpkh')
    print 'signed: {}'.format(signed_txhex)

    res = testlib.broadcast_transaction(signed_txhex)
    assert 'error' not in res

    return res


def scenario( wallets, **kw ): 
    resp = testlib.blockstack_namespace_preorder( "test", wallets[1].addr, wallets[0].privkey, tx_only=True)
    resp = send_as_segwit_bech32(resp['transaction'], wallets[0].privkey)

    testlib.next_block( **kw )

    # should not even be parsed, since it was sent from a bech32 address
    assert virtualchain.lib.indexer.StateEngine.get_block_statistics(testlib.get_current_block(**kw))['num_parsed_ops'] == 0
    assert virtualchain.lib.indexer.StateEngine.get_block_statistics(testlib.get_current_block(**kw))['num_processed_ops'] == 0


def check( state_engine ):
    
    # should not be preordered
    namespace_preorder_hashes = state_engine.get_all_preordered_namespace_hashes()
    if len(namespace_preorder_hashes) != 0:
        print "all hashes: %s" % namespace_preorder_hashes
        return False 

    return True

