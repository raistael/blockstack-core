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
    
    zonefile_batches = []

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
    
    # send initial subdomain zone files
    zonefiles = {
        'foo1.test': zf_template.format('foo1.test', subdomains.make_subdomain_txt('bar.foo1.test', 'foo1.test', wallets[4].addr, 0, zf_template.format('bar.foo1.test', zf_default_url), wallets[4].privkey)),
        'foo2.test': zf_template.format('foo2.test', subdomains.make_subdomain_txt('bar.foo2.test', 'foo2.test', wallets[4].addr, 0, zf_template.format('bar.foo2.test', zf_default_url), wallets[4].privkey)),
        'foo3.test': zf_template.format('foo3.test', subdomains.make_subdomain_txt('bar.foo3.test', 'foo3.test', wallets[4].addr, 0, zf_template.format('bar.foo3.test', zf_default_url), wallets[4].privkey)),
    }
    zonefile_batches.append(zonefiles)

    testlib.blockstack_name_register( "foo1.test", wallets[2].privkey, wallets[3].addr, zonefile_hash=storage.get_zonefile_data_hash(zonefiles['foo1.test']))
    testlib.blockstack_name_register( "foo2.test", wallets[2].privkey, wallets[3].addr, zonefile_hash=storage.get_zonefile_data_hash(zonefiles['foo2.test']))
    testlib.blockstack_name_register( "foo3.test", wallets[2].privkey, wallets[3].addr, zonefile_hash=storage.get_zonefile_data_hash(zonefiles['foo3.test']))
    testlib.blockstack_name_register( "foo4.test", wallets[2].privkey, wallets[3].addr, zonefile_hash='11' * 20)
    testlib.blockstack_name_register( "foo5.test", wallets[2].privkey, wallets[3].addr, zonefile_hash='11' * 20)
    testlib.blockstack_name_register( "foo6.test", wallets[2].privkey, wallets[3].addr, zonefile_hash='11' * 20)
    testlib.blockstack_name_register( "foo7.test", wallets[2].privkey, wallets[3].addr, zonefile_hash='11' * 20)
    testlib.next_block( **kw )
    
    # send updates too, but via a different name each time
    for i in range(0, 3):
        zf_template = "$ORIGIN {}\n$TTL 3600\n{}"
        zf_default_url = '_https._tcp URI 10 1 "https://test.com/?index={}"'.format(i+1)
        name = 'foo{}.test'.format(i + 4)

        zonefiles = {
            'foo1.test': zf_template.format(name, subdomains.make_subdomain_txt('bar.foo1.test', name, wallets[4].addr, i+1, zf_template.format('bar.foo1.test', zf_default_url), wallets[4].privkey)),
            'foo2.test': zf_template.format(name, subdomains.make_subdomain_txt('bar.foo2.test', name, wallets[4].addr, i+1, zf_template.format('bar.foo2.test', zf_default_url), wallets[4].privkey)),
            'foo3.test': zf_template.format(name, subdomains.make_subdomain_txt('bar.foo3.test', name, wallets[4].addr, i+1, zf_template.format('bar.foo3.test', zf_default_url), wallets[4].privkey)),
        }
        zonefile_batches.append(zonefiles)

        testlib.blockstack_name_update(name, storage.get_zonefile_data_hash(zonefiles['foo1.test']), wallets[3].privkey)
        testlib.blockstack_name_update(name, storage.get_zonefile_data_hash(zonefiles['foo2.test']), wallets[3].privkey)
        testlib.blockstack_name_update(name, storage.get_zonefile_data_hash(zonefiles['foo3.test']), wallets[3].privkey)
        testlib.next_block(**kw)

    # send all zonefiles at once
    for zfbatch in zonefile_batches:
        for name in zfbatch:
            assert testlib.blockstack_put_zonefile(zfbatch[name])

    # kick off subdomain indexing
    testlib.next_block(**kw)
    
    # query each subdomain
    for i in xrange(1, 4):
        fqn = 'bar.foo{}.test'.format(i)
        res = client.get_name_record(fqn, hostport='http://localhost:16264')
        if 'error' in res:
            print res
            return False
        
        # should all have domain foo6.test at this time
        if res['domain'] != 'foo6.test':
            print 'wrong domain'
            print res
            return False

        expected_zonefile = zf_template.format(fqn, zf_default_url)
        if base64.b64decode(res['zonefile']) != expected_zonefile:
            print 'zonefile mismatch'
            print 'expected\n{}'.format(expected_zonefile)
            print 'got\n{}'.format(base64.b64decode(res['zonefile']))
            return False

        # should be in atlas as well
        zf = testlib.blockstack_get_zonefile(res['value_hash'], parse=False)
        if not zf:
            print 'no zone file {} in atlas'.format(res['value_hash'])
            return False

        if zf != expected_zonefile:
            print 'zonefile mismatch in atlas'
            print 'expected\n{}'.format(expected_zonefile)
            print 'got\n{}'.format(base64.b64decode(res['zonefile']))
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
