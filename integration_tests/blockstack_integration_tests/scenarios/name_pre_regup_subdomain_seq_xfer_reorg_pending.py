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

# activate F-day 2017
"""
TEST ENV BLOCKSTACK_EPOCH_1_END_BLOCK 682
TEST ENV BLOCKSTACK_EPOCH_2_END_BLOCK 683
TEST ENV BLOCKSTACK_EPOCH_2_NAMESPACE_LIFETIME_MULTIPLIER 1
"""

import testlib
import virtualchain
import json
import blockstack
import blockstack.lib.subdomains as subdomains
import blockstack.lib.storage as storage
import blockstack.lib.client as client
import blockstack_zones
import base64

wallets = [
    testlib.Wallet( "5JesPiN68qt44Hc2nT8qmyZ1JDwHebfoh9KQ52Lazb1m1LaKNj9", 100000000000 ),
    testlib.Wallet( "5KHqsiU9qa77frZb6hQy9ocV7Sus9RWJcQGYYBJJBb2Efj1o77e", 100000000000 ),
    testlib.Wallet( "5Kg5kJbQHvk1B64rJniEmgbD83FpZpbw2RjdAZEzTefs9ihN3Bz", 100000000000 ),
    testlib.Wallet( "5JuVsoS9NauksSkqEjbUZxWwgGDQbMwPsEfoRBSpLpgDX1RtLX7", 100000000000 ),
    testlib.Wallet( "5KEpiSRr1BrT8vRD7LKGCEmudokTh1iMHbiThMQpLdwBwhDJB1T", 100000000000 )
]

consensus = "17ac43c1d8549c3181b200f1bf97eb7d"

def scenario( wallets, **kw ):

    testlib.blockstack_namespace_preorder( "test", wallets[1].addr, wallets[0].privkey )
    testlib.next_block( **kw )

    testlib.blockstack_namespace_reveal( "test", wallets[1].addr, 52595, 250, 4, [6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0], 10, 10, wallets[0].privkey )
    testlib.next_block( **kw )

    testlib.blockstack_namespace_ready( "test", wallets[1].privkey )
    testlib.next_block( **kw )

    testlib.blockstack_name_preorder( "foo1.test", wallets[2].privkey, wallets[3].addr )
    testlib.blockstack_name_preorder( "foo2.test", wallets[2].privkey, wallets[3].addr )
    testlib.blockstack_name_preorder( "foo3.test", wallets[2].privkey, wallets[3].addr )
    testlib.blockstack_name_preorder( "foo4.test", wallets[2].privkey, wallets[3].addr )
    testlib.blockstack_name_preorder( "foo5.test", wallets[2].privkey, wallets[3].addr )
    testlib.blockstack_name_preorder( "foo6.test", wallets[2].privkey, wallets[3].addr )
    testlib.blockstack_name_preorder( "foo7.test", wallets[2].privkey, wallets[3].addr )
    testlib.next_block( **kw )

    zf_template = "$ORIGIN {}\n$TTL 3600\n{}"
    zf_default_url = '_https._tcp URI 10 1 "https://raw.githubusercontent.com/nobody/content/profile.md"'

    zonefiles = {
        'foo1.test': zf_template.format('foo1.test', subdomains.make_subdomain_txt('bar.foo1.test', 'foo1.test', wallets[4].addr, 0, zf_template.format('bar.foo1.test', zf_default_url), wallets[4].privkey)),
        'foo2.test': zf_template.format('foo2.test', subdomains.make_subdomain_txt('bar.foo2.test', 'foo2.test', wallets[4].addr, 0, zf_template.format('bar.foo2.test', zf_default_url), wallets[4].privkey)),
        'foo3.test': zf_template.format('foo3.test', subdomains.make_subdomain_txt('bar.foo3.test', 'foo3.test', wallets[4].addr, 0, zf_template.format('bar.foo3.test', zf_default_url), wallets[4].privkey)),
    }

    testlib.blockstack_name_register( "foo1.test", wallets[2].privkey, wallets[3].addr, zonefile_hash=storage.get_zonefile_data_hash(zonefiles['foo1.test']))
    testlib.blockstack_name_register( "foo2.test", wallets[2].privkey, wallets[3].addr, zonefile_hash=storage.get_zonefile_data_hash(zonefiles['foo2.test']))
    testlib.blockstack_name_register( "foo3.test", wallets[2].privkey, wallets[3].addr, zonefile_hash=storage.get_zonefile_data_hash(zonefiles['foo3.test']))
    testlib.blockstack_name_register( "foo4.test", wallets[2].privkey, wallets[3].addr)
    testlib.blockstack_name_register( "foo5.test", wallets[2].privkey, wallets[3].addr)
    testlib.blockstack_name_register( "foo6.test", wallets[2].privkey, wallets[3].addr)
    testlib.blockstack_name_register( "foo7.test", wallets[2].privkey, wallets[3].addr)
    testlib.next_block( **kw )

    assert testlib.blockstack_put_zonefile(zonefiles['foo1.test'])
    assert testlib.blockstack_put_zonefile(zonefiles['foo2.test'])
    assert testlib.blockstack_put_zonefile(zonefiles['foo3.test'])
    
    # kick off indexing and check 
    testlib.next_block(**kw)

    def _query_subdomains(subdomain_names, expected_sequence, expected_owner, expect_pending):
        # query each subdomain.  Should get the latest
        for fqn in subdomain_names:
            res = client.get_name_record(fqn, hostport='http://localhost:16264')
            if 'error' in res:
                print res
                print 'failed to query {}'.format(fqn)
                return False
            
            # should have right sequence
            if res['sequence'] != expected_sequence:
                print 'wrong sequence; expected {}'.format(expected_sequence)
                print res
                return False
           
            # should have right owner
            if res['address'] != expected_owner:
                print 'wrong owner'
                print 'expected {}'.format(res['address'])
                print res
                return False

            # do we expect pending?
            if res['pending'] != expect_pending:
                print 'wrong pending (expected {})'.format(expect_pending)
                print res
                return False

        return True

    assert _query_subdomains(['bar.foo1.test', 'bar.foo2.test', 'bar.foo3.test'], 0, wallets[4].addr, False)
    
    expected_owners_before = [wallets[4].addr]
    expected_owners_after = [wallets[4].addr]

    # update and transfer, but if i % 2 == 0, transfer to a different address
    # use a different domain name in each case.
    # verify that only transfers on the creator domain are valid.
    wallet_schedule = [
        (4, 0),  # not broadcast initially 
        (4, 1),
        (0, 1),  # not broadcast initially
        (1, 2),
    ]
    sequence_schedule = [
        1,
        1,
        2,
        2,
    ]

    expected_zf_default_url = '_https._tcp URI 10 1 "https://test.com/?index={}"'.format(4)
    expect_pending = False
    expect_sequence = 0
    expect_owner = wallets[4].addr

    unsent_zonefiles = []

    # send updates too, and transfer subdomains
    for i in range(0, 4):
        zf_template = "$ORIGIN {}\n$TTL 3600\n{}"
        zf_default_url = '_https._tcp URI 10 1 "https://test.com/?index={}"'.format(i+1)

        names = [
            'foo1.test',
            'foo2.test',
            'foo3.test',
        ]

        k = wallet_schedule[i][0]
        k2 = wallet_schedule[i][1]
        s = sequence_schedule[i]

        zonefiles = {
            'foo1.test': zf_template.format(names[0], subdomains.make_subdomain_txt('bar.foo1.test', names[0], wallets[k2].addr, s, zf_template.format('bar.foo1.test', zf_default_url), wallets[k].privkey)),
            'foo2.test': zf_template.format(names[1], subdomains.make_subdomain_txt('bar.foo2.test', names[1], wallets[k2].addr, s, zf_template.format('bar.foo2.test', zf_default_url), wallets[k].privkey)),
            'foo3.test': zf_template.format(names[2], subdomains.make_subdomain_txt('bar.foo3.test', names[2], wallets[k2].addr, s, zf_template.format('bar.foo3.test', zf_default_url), wallets[k].privkey)),
        }
        
        testlib.blockstack_name_update(names[0], storage.get_zonefile_data_hash(zonefiles['foo1.test']), wallets[3].privkey)
        testlib.blockstack_name_update(names[1], storage.get_zonefile_data_hash(zonefiles['foo2.test']), wallets[3].privkey)
        testlib.blockstack_name_update(names[2], storage.get_zonefile_data_hash(zonefiles['foo3.test']), wallets[3].privkey)
        testlib.next_block(**kw)

        if i % 2 == 1:
            # only broadcast periodically
            assert testlib.blockstack_put_zonefile(zonefiles['foo1.test'])
            assert testlib.blockstack_put_zonefile(zonefiles['foo2.test'])
            assert testlib.blockstack_put_zonefile(zonefiles['foo3.test'])
            expect_owner = wallets[k2].addr
            expect_sequence += 1
            expected_owners_before.append(expect_owner)

        else:
            expect_pending = True
            unsent_zonefiles.append(zonefiles)
            expected_owners_after.append(wallets[k2].addr)
    
        # kick off subdomain indexing
        testlib.next_block(**kw)

        # verify history
        assert _query_subdomains(['bar.foo1.test', 'bar.foo2.test', 'bar.foo3.test'], expect_sequence, expect_owner, expect_pending)
        
    
    # query subdomain history
    for subd in ['bar.foo1.test', 'bar.foo2.test', 'bar.foo3.test']:
        res = client.get_name_record(subd, include_history=True, hostport='http://localhost:16264')
        if 'error' in res:
            print res
            return False

        if not res['pending']:
            print 'not pending, but it should be'
            print res
            return False
       
        # should be at 2
        if res['sequence'] != 2:
            print 'wrong sequence'
            print res
            return False

        if virtualchain.address_reencode(str(res['address'])) != virtualchain.address_reencode(expect_owner):
            print 'wrong owner'
            print res
            return False

        for i, block_height in enumerate(sorted(res['history'])):
            if virtualchain.address_reencode(str(res['history'][block_height][0]['address'])) != virtualchain.address_reencode(expected_owners_before[i]):
                print 'wrong owner at {}: expected {}'.format(block_height, expected_owners_before[i])
                print json.dumps(res, indent=4, sort_keys=True)
                print expected_owners_before
                return False

            if res['history'][block_height][0]['sequence'] != i:
                print 'wrong sequence at {}: expected {}'.format(block_height, i)
                print json.dumps(res, indent=4, sort_keys=True)
                return False

    # send all missing subdomains.
    # should cause a cascading owner reorg.
    for zfbatch in unsent_zonefiles:
        for k in zfbatch:
            assert testlib.blockstack_put_zonefile(zfbatch[k])

    testlib.next_block(**kw)

    # query subdomain history again.  pending and owner should change
    for subd in ['bar.foo1.test', 'bar.foo2.test', 'bar.foo3.test']:
        res = client.get_name_record(subd, include_history=True, hostport='http://localhost:16264')
        if 'error' in res:
            print res
            return False

        if res['pending']:
            print 'pending, but it should not be'
            print res
            return False

        if res['sequence'] != 2:
            print 'wrong sequence'
            print res
            return False

        if virtualchain.address_reencode(str(res['address'])) != virtualchain.address_reencode(wallets[1].addr):
            print 'wrong owner again'
            print res
            return False

        for i, block_height in enumerate(sorted(res['history'])):
            if virtualchain.address_reencode(str(res['history'][block_height][0]['address'])) != virtualchain.address_reencode(str(expected_owners_after[i])):
                print 'wrong owner at {}: expected {}'.format(block_height, expected_owners_after[i])
                print json.dumps(res, indent=4, sort_keys=True)
                print expected_owners_after
                print expected_owners_before
                print [wallets[i].addr for i in range(0, len(wallets))]
                return False

            if res['history'][block_height][0]['sequence'] != i:
                print 'wrong sequence at {}: expected {}'.format(block_height, i)
                print json.dumps(res, indent=4, sort_keys=True)
                return False

    # reindex
    assert testlib.check_subdomain_db(**kw)


def check( state_engine ):

    # not revealed, but ready 
    ns = state_engine.get_namespace_reveal( "test" )
    if ns is not None:
        return False 

    ns = state_engine.get_namespace( "test" )
    if ns is None:
        return False 

    if ns['namespace_id'] != 'test':
        return False 

    for i in xrange(1, 4):
        name = 'foo{}.test'.format(i)

        # not preordered
        preorder = state_engine.get_name_preorder( name, virtualchain.make_payment_script(wallets[2].addr), wallets[3].addr )
        if preorder is not None:
            print 'still have preorder: {}'.format(preorder)
            return False
         
        # registered 
        name_rec = state_engine.get_name(name)
        if name_rec is None:
            print 'did not get name {}'.format(name)
            return False

        # owned by
        if name_rec['address'] != wallets[3].addr or name_rec['sender'] != virtualchain.make_payment_script(wallets[3].addr):
            print 'wrong address for {}: {}'.format(name, name_rec)
            return False

    return True
