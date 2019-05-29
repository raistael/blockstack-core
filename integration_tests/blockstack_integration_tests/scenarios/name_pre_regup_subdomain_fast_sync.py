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
TEST ENV BLOCKSTACK_EPOCH_3_NAMESPACE_LIFETIME_MULTIPLIER 1
TEST ENV BLOCKSTACK_EPOCH_3_NAMESPACE_LIFETIME_GRACE_PERIOD 1
"""

import os
import shutil
import testlib
import virtualchain
import blockstack
import blockstack_zones
import virtualchain
import json
import time
from blockstack.lib import subdomains

wallets = [
    testlib.Wallet( "5JesPiN68qt44Hc2nT8qmyZ1JDwHebfoh9KQ52Lazb1m1LaKNj9", 100000000000 ),
    testlib.Wallet( "5KHqsiU9qa77frZb6hQy9ocV7Sus9RWJcQGYYBJJBb2Efj1o77e", 100000000000 ),
    testlib.Wallet( "5Kg5kJbQHvk1B64rJniEmgbD83FpZpbw2RjdAZEzTefs9ihN3Bz", 100000000000 ),
    testlib.Wallet( "5JuVsoS9NauksSkqEjbUZxWwgGDQbMwPsEfoRBSpLpgDX1RtLX7", 100000000000 ),
    testlib.Wallet( "5KEpiSRr1BrT8vRD7LKGCEmudokTh1iMHbiThMQpLdwBwhDJB1T", 100000000000 ),
    testlib.Wallet( "5K6Nou64uUXg8YzuiVuRQswuGRfH1tdb9GUC9NBEV1xmKxWMJ54", 100000000000 )
]

consensus = "17ac43c1d8549c3181b200f1bf97eb7d"
value_hashes = []
namespace_ids = []

def restore( working_dir, snapshot_path, restore_dir, pubkeys, num_required ):
    
    global value_hashes

    if os.path.exists(restore_dir):
        shutil.rmtree(restore_dir)

    os.makedirs(restore_dir)

    rc = blockstack.fast_sync_import( restore_dir, "file://{}".format(snapshot_path), public_keys=pubkeys, num_required=num_required )
    if not rc:
        print "failed to restore snapshot {}".format(snapshot_path)
        return False

    # database must be identical 
    db_filenames = ['blockstack-server.db', 'blockstack-server.snapshots', 'atlas.db', 'subdomains.db', 'subdomains.db.queue']
    src_paths = [os.path.join(working_dir, fn) for fn in db_filenames]
    backup_paths = [os.path.join(restore_dir, fn) for fn in db_filenames]

    for src_path, backup_path in zip(src_paths, backup_paths):
        rc = os.system('echo ".dump" | sqlite3 "{}" > "{}/first.dump"; echo ".dump" | sqlite3 "{}" > "{}/second.dump"; cmp "{}/first.dump" "{}/second.dump"'.format(
            src_path, restore_dir, backup_path, restore_dir, restore_dir, restore_dir))

        if rc != 0:
            print '{} disagress with {}'.format(src_path, backup_path)
            return False
    
    # all zone files must be present
    for vh in value_hashes:
        zfdata = blockstack.get_atlas_zonefile_data(vh, os.path.join(restore_dir, 'zonefiles'))
        if zfdata is None:
            print 'Missing {} in {}'.format(vh, os.path.join(restore_dir, 'zonefiles'))
            return False
    
    # all import keychains must be present
    for ns in namespace_ids:
        import_keychain_path = blockstack.lib.namedb.BlockstackDB.get_import_keychain_path(restore_dir, ns)
        if not os.path.exists(import_keychain_path):
            print 'Missing import keychain {}'.format(import_keychain_path)
            return False

    return True


def scenario( wallets, **kw ):

    global value_hashes

    testlib.blockstack_namespace_preorder( "test", wallets[1].addr, wallets[0].privkey )
    testlib.next_block( **kw )

    testlib.blockstack_namespace_reveal( "test", wallets[1].addr, 52595, 250, 4, [6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0], 10, 10, wallets[0].privkey )
    testlib.next_block( **kw )

    testlib.blockstack_namespace_ready( "test", wallets[1].privkey )
    testlib.next_block( **kw )

    # register 10 names
    for i in xrange(0, 10):
        res = testlib.blockstack_name_preorder( "foo_{}.test".format(i), wallets[2].privkey, wallets[3].addr )
        if 'error' in res:
            print json.dumps(res)
            return False

    testlib.next_block( **kw )
   
    # make some subdomains
    zf_template = "$ORIGIN {}\n$TTL 3600\n{}"
    zf_default_url = '_https._tcp URI 10 1 "https://raw.githubusercontent.com/nobody/content/profile.md"'

    zonefiles = {
        'foo_0.test': zf_template.format('foo_0.test', subdomains.make_subdomain_txt('bar.foo_0.test', 'foo_0.test', wallets[4].addr, 0, zf_template.format('bar.foo_0.test', zf_default_url), wallets[4].privkey)),
        'foo_1.test': zf_template.format('foo_1.test', subdomains.make_subdomain_txt('bar.foo_1.test', 'foo_1.test', wallets[4].addr, 0, zf_template.format('bar.foo_1.test', zf_default_url), wallets[4].privkey)),
        'foo_2.test': zf_template.format('foo_2.test', subdomains.make_subdomain_txt('bar.foo_2.test', 'foo_2.test', wallets[4].addr, 0, zf_template.format('bar.foo_2.test', zf_default_url), wallets[4].privkey)),
        'foo_3.test': zf_template.format('foo_3.test', subdomains.make_subdomain_txt('bar.foo_3.test', 'foo_3.test', wallets[4].addr, 0, zf_template.format('bar.foo_3.test', zf_default_url), wallets[4].privkey)),
        'foo_4.test': zf_template.format('foo_4.test', subdomains.make_subdomain_txt('bar.foo_4.test', 'foo_4.test', wallets[4].addr, 0, zf_template.format('bar.foo_4.test', zf_default_url), wallets[4].privkey)),
        'foo_5.test': zf_template.format('foo_5.test', subdomains.make_subdomain_txt('bar.foo_5.test', 'foo_5.test', wallets[4].addr, 0, zf_template.format('bar.foo_5.test', zf_default_url), wallets[4].privkey)),
        'foo_6.test': zf_template.format('foo_6.test', subdomains.make_subdomain_txt('bar.foo_6.test', 'foo_6.test', wallets[4].addr, 0, zf_template.format('bar.foo_6.test', zf_default_url), wallets[4].privkey)),
        'foo_7.test': zf_template.format('foo_7.test', subdomains.make_subdomain_txt('bar.foo_7.test', 'foo_7.test', wallets[4].addr, 0, zf_template.format('bar.foo_7.test', zf_default_url), wallets[4].privkey)),
        'foo_8.test': zf_template.format('foo_8.test', subdomains.make_subdomain_txt('bar.foo_8.test', 'foo_8.test', wallets[4].addr, 0, zf_template.format('bar.foo_8.test', zf_default_url), wallets[4].privkey)),
        'foo_9.test': zf_template.format('foo_9.test', subdomains.make_subdomain_txt('bar.foo_9.test', 'foo_9.test', wallets[4].addr, 0, zf_template.format('bar.foo_9.test', zf_default_url), wallets[4].privkey)),
    }
    
    for i in xrange(0, 10):
        res = testlib.blockstack_name_register( "foo_{}.test".format(i), wallets[2].privkey, wallets[3].addr, zonefile_hash=blockstack.lib.storage.get_zonefile_data_hash(zonefiles['foo_{}.test'.format(i)]))
        if 'error' in res:
            print json.dumps(res)
            return False

    testlib.next_block( **kw )
 
    # propagate the first five subdomains 
    for i in range(0,5):
        name = 'foo_{}.test'.format(i)
        assert testlib.blockstack_put_zonefile(zonefiles[name])
    
    # process the first five subdomains
    testlib.next_block( **kw )

    # propagate the last five subdomains, but don't process them
    for i in range(5,10):
        name = 'foo_{}.test'.format(i)
        assert testlib.blockstack_put_zonefile(zonefiles[name])

    print 'waiting for all zone files to replicate'
    time.sleep(10)

    working_dir = os.environ.get('BLOCKSTACK_WORKING_DIR')
    restore_dir = os.path.join(working_dir, "snapshot_dir")

    # make a backup 
    db = testlib.get_state_engine()

    print 'begin make backups of state from {}'.format(testlib.get_current_block(**kw) - 1)
    for name in os.listdir(os.path.join(working_dir, 'backups')):
        if name.endswith('.{}'.format(testlib.get_current_block(**kw) - 1)):
            os.unlink(os.path.join(working_dir, 'backups', name))

    db.make_backups(testlib.get_current_block(**kw))
    print 'end make backups'

    def _backup_and_restore():
        # snapshot the latest backup
        snapshot_path = os.path.join(working_dir, "snapshot.bsk" )
        rc = blockstack.fast_sync_snapshot(working_dir, snapshot_path, wallets[3].privkey, None )
        if not rc:
            print "Failed to fast_sync_snapshot"
            return False
       
        if not os.path.exists(snapshot_path):
            print "Failed to create snapshot {}".format(snapshot_path)
            return False

        # sign with more keys 
        for i in xrange(4, 6):
            rc = blockstack.fast_sync_sign_snapshot( snapshot_path, wallets[i].privkey )
            if not rc:
                print "Failed to sign with key {}".format(i)
                return False

        # restore!
        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[3].pubkey_hex, wallets[4].pubkey_hex, wallets[5].pubkey_hex], 3 )
        if not rc:
            print "1 failed to restore snapshot {}".format(snapshot_path)
            return False

        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[5].pubkey_hex, wallets[4].pubkey_hex, wallets[3].pubkey_hex], 3 )
        if not rc:
            print "2 failed to restore snapshot {}".format(snapshot_path)
            return False

        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[3].pubkey_hex, wallets[4].pubkey_hex], 2 )
        if not rc:
            print "3 failed to restore snapshot {}".format(snapshot_path)
            return False

        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[3].pubkey_hex, wallets[5].pubkey_hex], 2 )
        if not rc:
            print "4 failed to restore snapshot {}".format(snapshot_path)
            return False

        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[4].pubkey_hex, wallets[5].pubkey_hex], 2 )
        if not rc:
            print "5 failed to restore snapshot {}".format(snapshot_path)
            return False

        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[3].pubkey_hex], 1 )
        if not rc:
            print "6 failed to restore snapshot {}".format(snapshot_path)
            return False

        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[4].pubkey_hex, wallets[0].pubkey_hex], 1 )
        if not rc:
            print "7 failed to restore snapshot {}".format(snapshot_path)
            return False

        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[0].pubkey_hex, wallets[1].pubkey_hex, wallets[5].pubkey_hex], 1 )
        if not rc:
            print "8 failed to restore snapshot {}".format(snapshot_path)
            return False

        shutil.move(restore_dir, restore_dir + '.bak')

        # should fail
        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[3].pubkey_hex], 2 )
        if rc:
            print "restored insufficient signatures snapshot {}".format(snapshot_path)
            return False

        shutil.rmtree(restore_dir)

        # should fail
        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[3].pubkey_hex, wallets[4].pubkey_hex], 3 )
        if rc:
            print "restored insufficient signatures snapshot {}".format(snapshot_path)
            return False

        shutil.rmtree(restore_dir)

        # should fail
        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[0].pubkey_hex], 1 )
        if rc:
            print "restored wrongly-signed snapshot {}".format(snapshot_path)
            return False

        shutil.rmtree(restore_dir)

        # should fail
        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[0].pubkey_hex, wallets[3].pubkey_hex], 2 )
        if rc:
            print "restored wrongly-signed snapshot {}".format(snapshot_path)
            return False

        shutil.rmtree(restore_dir)

        # should fail
        rc = restore( kw['working_dir'], snapshot_path, restore_dir, [wallets[0].pubkey_hex, wallets[3].pubkey_hex, wallets[4].pubkey_hex], 3 )
        if rc:
            print "restored wrongly-signed snapshot {}".format(snapshot_path)
            return False

        shutil.rmtree(restore_dir)
        shutil.move(restore_dir + '.bak', restore_dir)
        return True

    # test backup and restore
    res = _backup_and_restore()
    if not res:
        return res

    # first five subdomains are all present in the subdomain DB 
    subds = ['bar.foo_{}.test'.format(i) for i in range(0,5)]
    subdomain_db = blockstack.lib.subdomains.SubdomainDB(os.path.join(restore_dir, 'subdomains.db'), os.path.join(restore_dir, 'zonefiles'))
    for subd in subds:
        rec = subdomain_db.get_subdomain_entry(subd)
        if not rec:
            print 'not found: {}'.format(subd)
            return False
        
    # last 5 subdomains are queued in the subdomain DB queue 
    queued_zfinfos = blockstack.lib.queue.queuedb_findall(os.path.join(restore_dir, 'subdomains.db.queue'), 'zonefiles')
    if len(queued_zfinfos) != 5:
        print 'only {} zonefiles queued'.format(queued_zfinfos)
        print queued_zfinfos
        return False

    # process the last five subdomains
    testlib.next_block( **kw )

    shutil.rmtree(restore_dir)
    os.unlink(os.path.join(working_dir, "snapshot.bsk"))

    # test backup and restore
    res = _backup_and_restore()
    if not res:
        return res
    
    # all subdomains are all present in the subdomain DB 
    subds = ['bar.foo_{}.test'.format(i) for i in range(0,10)]
    subdomain_db = blockstack.lib.subdomains.SubdomainDB(os.path.join(restore_dir, 'subdomains.db'), os.path.join(restore_dir, 'zonefiles'))
    for subd in subds:
        rec = subdomain_db.get_subdomain_entry(subd)
        if not rec:
            print 'not found: {}'.format(subd)
            return False

    # nothing queued
    queued_zfinfos = blockstack.lib.queue.queuedb_findall(os.path.join(restore_dir, 'subdomains.db.queue'), 'zonefiles')
    if len(queued_zfinfos) != 0:
        print '{} zonefiles queued'.format(queued_zfinfos)
        print queued_zfinfos
        return False

    shutil.rmtree(restore_dir)

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

    for i in xrange(0, 10):
        name = 'foo_{}.test'.format(i)
        # not preordered
        preorder = state_engine.get_name_preorder( name, virtualchain.make_payment_script(wallets[2].addr), wallets[3].addr )
        if preorder is not None:
            print "still have preorder"
            return False
        
        # registered 
        name_rec = state_engine.get_name( name )
        if name_rec is None:
            print "name does not exist"
            return False 

        # owned 
        if name_rec['address'] != wallets[3].addr or name_rec['sender'] != virtualchain.make_payment_script(wallets[3].addr):
            print "name has wrong owner"
            return False 

        # updated 
        if name_rec['value_hash'] is None:
            print "wrong value hash: %s" % name_rec['value_hash']
            return False 

    return True
