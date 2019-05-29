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

import testlib
import virtualchain
import blockstack

# activate tokens
"""
TEST ENV BLOCKSTACK_EPOCH_1_END_BLOCK 682
TEST ENV BLOCKSTACK_EPOCH_2_END_BLOCK 683
TEST ENV BLOCKSTACK_EPOCH_3_END_BLOCK 684
TEST ENV BLOCKSTACK_EPOCH_2_NAMESPACE_LIFETIME_MULTIPLIER 1
TEST ENV BLOCKSTACK_EPOCH_3_NAMESPACE_LIFETIME_MULTIPLIER 1
TEST ENV BLOCKSTACK_EPOCH_3_NAMESPACE_RECEIVE_FEES_PERIOD 5
TEST ENV BLOCKSTACK_EPOCH_4_NAMESPACE_RECEIVE_FEES_PERIOD 5
"""

wallets = [
    testlib.Wallet( "5JesPiN68qt44Hc2nT8qmyZ1JDwHebfoh9KQ52Lazb1m1LaKNj9", 100000000000 ),
    testlib.Wallet( "5KHqsiU9qa77frZb6hQy9ocV7Sus9RWJcQGYYBJJBb2Efj1o77e", 100000000000 ),
    testlib.Wallet( "5Kg5kJbQHvk1B64rJniEmgbD83FpZpbw2RjdAZEzTefs9ihN3Bz", 100000000000 ),
    testlib.Wallet( "5JuVsoS9NauksSkqEjbUZxWwgGDQbMwPsEfoRBSpLpgDX1RtLX7", 100000000000 ),
    testlib.Wallet( "5KEpiSRr1BrT8vRD7LKGCEmudokTh1iMHbiThMQpLdwBwhDJB1T", 100000000000 ),
    testlib.Wallet("9864768ccf5137392de5b5d6551a0f9f17279df2f82b4de7b905290f95fde66201", 0),
    testlib.Wallet("2e55007fec0f1d9a81700e56aa8ce24d7e6e245ede48c00663f930f99fae133601", 0),
    testlib.Wallet("9d6836cdaf81245d646988effe398338073892143b1185f4553e6118f231d1bf01", 0),
    testlib.Wallet("f9c9371b7a8cc6b5ef544457cdd565e5791d743f5d60c924265732147429414801", 0),
    testlib.Wallet("cd8d6bdf3dfd7b3d498539bb42cf218b77b0fda4f3bc119c7226d803e8425da901", 0), 
]

consensus = "17ac43c1d8549c3181b200f1bf97eb7d"
pk = wallets[-1].privkey
pk2 = wallets[-2].privkey

def scenario( wallets, **kw ):
    global pk, pk2

    testlib.blockstack_namespace_preorder( "test", wallets[1].addr, wallets[0].privkey )
    testlib.next_block( **kw )

    testlib.blockstack_namespace_reveal( "test", wallets[1].addr, 52595, 250, 4, [6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0], 10, 10, wallets[0].privkey, version_bits=blockstack.lib.config.NAMESPACE_VERSION_PAY_TO_CREATOR)
    testlib.next_block( **kw )

    testlib.blockstack_namespace_ready( "test", wallets[1].privkey )
    testlib.next_block( **kw )

    # pay for a name in a v1 namespace with Stacks
    addr = virtualchain.address_reencode(virtualchain.get_privkey_address(pk))
    addr2 = virtualchain.address_reencode(virtualchain.get_privkey_address(pk2))

    # calculate the cost of doing so
    namespace = testlib.get_state_engine().get_namespace('test')
    stacks_price = blockstack.lib.scripts.price_name_stacks('foo', namespace, testlib.get_current_block(**kw))
    btc_price = blockstack.lib.scripts.price_name('foo', namespace, testlib.get_current_block(**kw))

    print ''
    print 'price of {} in Stacks is {}'.format('foo.test', stacks_price)
    print ''

    testlib.blockstack_send_tokens(addr, "STACKS", stacks_price + 1, wallets[0].privkey)
    testlib.blockstack_send_tokens(addr2, "STACKS", stacks_price + 1, wallets[0].privkey)
    testlib.send_funds(wallets[0].privkey, btc_price - 5500 - 1, addr)  # deliberately insufficient funds for ordering the name in BTC
    testlib.send_funds(wallets[0].privkey, btc_price - 5500 - 1, addr2)  # deliberately insufficient funds for ordering the name in BTC
    testlib.next_block(**kw)
    testlib.next_block(**kw)
    testlib.next_block(**kw)
    testlib.next_block(**kw)    # move beyond pay-to-creator requirement

    # preorder/register using Stacks, but overpay (foo.test fails, bar.test succeeds)
    testlib.blockstack_name_preorder( "foo.test", pk, wallets[3].addr, price={'units': 'STACKS', 'amount': stacks_price + 2}, expect_fail=True, safety_checks=False)
    testlib.blockstack_name_preorder( "bar.test", pk2, wallets[3].addr, price={'units': 'STACKS', 'amount': stacks_price + 1})
    testlib.next_block( **kw )
    testlib.expect_snv_fail_at('foo.test', testlib.get_current_block(**kw))

    testlib.send_funds(wallets[0].privkey, btc_price - 5500 - 1, addr)  # deliberately insufficient funds for ordering the name in BTC
    testlib.send_funds(wallets[0].privkey, btc_price - 5500 - 1, addr2)  # deliberately insufficient funds for ordering the name in BTC
    testlib.blockstack_name_register( "foo.test", pk, wallets[3].addr ) # should fail
    testlib.blockstack_name_register( "bar.test", pk2, wallets[3].addr ) # should succeed
    testlib.next_block( **kw )
    testlib.expect_snv_fail_at('foo.test', testlib.get_current_block(**kw))


def check( state_engine ):

    # not revealed, but ready 
    ns = state_engine.get_namespace_reveal( "test" )
    if ns is not None:
        print "namespace reveal exists"
        return False 

    ns = state_engine.get_namespace( "test" )
    if ns is None:
        print "no namespace"
        return False 

    if ns['namespace_id'] != 'test':
        print "wrong namespace"
        return False 

    # not preordered
    addr = virtualchain.address_reencode(virtualchain.get_privkey_address(pk))
    addr2 = virtualchain.address_reencode(virtualchain.get_privkey_address(pk2))
    preorder = state_engine.get_name_preorder( "foo.test", virtualchain.make_payment_script(addr), wallets[3].addr )
    if preorder is not None:
        print "preorder exists for foo.test"
        return False
    
    # not registered 
    name_rec = state_engine.get_name( "foo.test" )
    if name_rec is not None:
        print "name exists"
        return False 

    # not preordered
    preorder = state_engine.get_name_preorder('bar.test', virtualchain.make_payment_script(addr2), wallets[3].addr)
    if preorder is not None:
        print 'preorder exists for bar.test'
        return False

    # registered
    name_rec = state_engine.get_name('bar.test')
    if name_rec is None:
        print 'bar.test does not exist'
        return False

    # owned
    if name_rec['address'] != wallets[3].addr or name_rec['sender'] != virtualchain.make_payment_script(wallets[3].addr):
        print 'bar.test not owned'
        return False

    # overpaid
    if name_rec['op_fee'] > 5500 or name_rec['token_fee'] != blockstack.lib.scripts.price_name_stacks('bar', ns, state_engine.lastblock) + 1:
        print 'bar.test improperly paid'
        return False

    return True
