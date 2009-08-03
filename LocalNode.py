from __future__ import with_statement

import datetime, md5, threading, operator, types
import Utils, Tables, Node

debug_sync = True
debug_sync_event_wait = False
debug_sync_connect = False
reconnect_delay = 10.0

class HostedNode(Node.Node):
    def __init__(self, _conn, node_id, host):
        self.host = host
        Node.Node.__init__(self, _conn, node_id)

class SyncNode(HostedNode):
    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    # Sync peers locally (where both are LocalNode:s). Note that we
    # introduce disorder in the syncing order to crack loops.
    # However we're lazy and don't use real randomness, which we should...
    _sync_peers_locally_offset = 0
    def sync_peers_locally(self, other):
        fns = [self.sync_self, other.sync_self, lambda: self.sync_peer(other, True), lambda: self.sync_peer(other, False)]
        off = self._sync_peers_locally_offset
        fns = fns[off:] + fns[:off]
        self._sync_peers_locally_offset = (off + 1) % 4
        return reduce(operator.add, (x() for x in fns))

    def sync_peers(self, other):
        return self.sync_peer(other, True) + self.sync_peer(other, False)

    def sync_peer(self, other, send = True):
        if not send:
            self, other = other, self

        subscription, message, delete_subscription = self.get_subscription_update(other.node_id)
        if debug_sync:
            print "Sync: %s -> %s : %s, %s, delete:%s" % (self.id2s(self.node_id), self.id2s(other.node_id), subscription, message, delete_subscription)
        if subscription:
            if delete_subscription:
                other.delete_subscription(subscription)
            else:
                # Yes, ignore result if syncing self, just pretend we did an update
                if self.node_id != other.node_id:
                    if message:
                        other.register_message(message, subscription)
                    else:
                        other.update_subscription(subscription)
            return 1
        return 0

    def sync_self(self):
        return self.sync_peer(self)

    def connect_peers(self, other):
        for peers in Utils.bidirectional(self, other):
            peers[0].register_peer(peers[1].get_local_node())

    def import_message_from_peer(self, other, message_id):
        self.connect_peers(other)
        message = other.get_message(message_id)
        self.register_message(
            message,
            {'peer_id': other.node_id,
             'message_id': message['message_id']})
        self.update_local_subscription(message, 0)

    def get_peers(self, *arg, **kw):
        return [obj['peer_id']
                for obj in Tables.Peer.select_objs(self._conn, self.node_id, *arg, **kw)]

    def get_peer(self, peer_id):
        # Add XMLL-RPC connect interface here...
        return self.LocalPeerConnector(self.host.get_node(peer_id))

    class LocalPeerConnector(object):
        def __init__(self, local_peer):
            self._local_peer = local_peer
            
        def __getattribute__(self, name):
            if not hasattr(Node.Node, name):
                raise AttributeError("You can not use methods meant for the local node on peers, even when connected to them locally.", name)

            def wrap(local, member):
                def wrapper(*arg, **kw):
                    try:
                        try:
                            return member(*arg, **kw)
                        except:
                            local.rollback()
                    finally:
                        local.commit()
                return wrapper

            local = object.__getattribute__(self, "_local_peer")
            member = getattr(local, name)
            if not isinstance(member, types.MethodType):
                return member
            return wrap(local, member)


class ThreadSyncNode(SyncNode):
    def __init__(self, *arg, **kw):
        super(ThreadSyncNode, self).__init__(*arg, **kw)
        self._sync_new_event = threading.Condition()
        self._sync_outbound_shutdown = False
        self.sync_peers = []
        self.sync_outbound_thread = self.OutboundSyncThread(self)
        self.sync_outbound_connection_manager_thread = self.OutboundConnectionManagerThread(self)

    def commit(self):
        print "commit:%s:commit" % threading.currentThread().getName() 
        SyncNode.commit(self)
        print "commit:%s:sync_signal_event" % threading.currentThread().getName() 
        self.sync_signal_event()

    def sync_start(self):
        self.sync_outbound_thread.start()
        self.sync_outbound_connection_manager_thread.start()
        
    def sync_stop(self):
        self._sync_outbound_shutdown = True
        self.sync_signal_event()

    def sync_wait_for_event(self, timeout = None):
        print "sync_wait_for_event:%s:acquire" % threading.currentThread().getName() 
        self._sync_new_event.acquire()
        print "sync_wait_for_event:%s:wait" % threading.currentThread().getName() 
        self._sync_new_event.wait(timeout)
        print "sync_wait_for_event:%s:release" % threading.currentThread().getName() 
        self._sync_new_event.release()

    def sync_signal_event(self):
        print "sync_signal_event:%s:acquire" % threading.currentThread().getName() 
        self._sync_new_event.acquire()
        print "sync_signal_event:%s:notifyAll" % threading.currentThread().getName() 
        self._sync_new_event.notifyAll()
        print "sync_signal_event:%s:release" % threading.currentThread().getName() 
        self._sync_new_event.release()

    def sync_add_peer(self, peer):
        self.sync_peers.append(peer)
        self.sync_signal_event()

    def sync_remove_peer(self, peer):
        self.sync_peers.remove(peer)
        self.sync_signal_event()

    class OutboundConnectionManagerThread(threading.Thread):
        def __init__(self, node, *arg, **kw):
            self.node = node
            threading.Thread.__init__(
                self, name = "OutboundConnectionManagerThread for %s" % (node.node_id,), *arg, **kw)

        #FIXME: Handle commits for local node, and handle commits for local peers somehow

        def run(self):
            print "%s: Starting...." % self.getName()
            while not self.node._sync_outbound_shutdown:
                peer_ids = [peer.node_id for peer in self.node.sync_peers]
                if not peer_ids:
                    sql = 'true'
                elif len(peer_ids) == 1:
                    sql = 'peer_id != %s'
                else:
                    sql = 'peer_id not in (%s)' % (', '.join('%s' for peer_id in peer_ids),)
                non_connected_peers = self.node.get_peers(_query_sql=(sql, peer_ids))
                for peer_id in non_connected_peers:
                    peer = self.node.get_peer(peer_id)
                    if peer:
                        if debug_sync_connect: print "%s: Connected to peer: %s" % (self.getName(), peer_id)
                        self.node.sync_add_peer(peer)
                    else:
                        if debug_sync_connect: print "%s: Unable to connect to peer: %s" % (self.getName(), peer_id)
                    if self.node._sync_outbound_shutdown: return                
                if debug_sync_event_wait: print "%s: Waiting..." % (self.getName(),)
                self.node.sync_wait_for_event(reconnect_delay)

    class OutboundSyncThread(threading.Thread):
        def __init__(self, node, *arg, **kw):
            self.node = node
            threading.Thread.__init__(
                self, name = "OutboundSyncThread for %s" % (node.node_id,), *arg, **kw)

        def run(self):
            print "%s: Starting...." % self.getName()
            while not self.node._sync_outbound_shutdown:
                syncs = 0
                for peer in list(self.node.sync_peers): # Copy to avoid list changing under our feet...
                    try:
                        syncs += self.node.sync_peer(peer)
                    except:
                        import traceback
                        traceback.print_exc()
                        self.node.sync_remove_peer(peer)
                    if self.node._sync_outbound_shutdown: return
                self.node.sync_self()
                if self.node._sync_outbound_shutdown: return
                if not syncs:
                    if debug_sync_event_wait: print "%s: Waiting..." % (self.getName(),)
                    self.node.sync_wait_for_event()

class IntrospectionNode(Node.Node):
    def _get_messages(self, **kw):
        return Tables.Message.select_objs(self._conn, node_id = self.node_id, **kw)

    def _get_local_subscriptions(self, **kw):
        return Tables.LocalSubscription.select_objs(self._conn, node_id = self.node_id, **kw)

    def _get_subscriptions(self, **kw):
        return Tables.Subscription.select_objs(self._conn, node_id = self.node_id, **kw)

    def _get_message_links(self, **kw):
        return Tables.MessageLink.select_objs(self._conn, node_id = self.node_id, **kw)


class UINode(Node.Node):
    def post_message(self, message):
        message['message_id'] = self.calculate_message_id(message)
        message['message_challenge'] = self.calculate_message_challenge(message)
        self._register_message(message)
        self.update_local_subscription(message)
        return message

    def update_local_subscription(self, message, subscribed = 1):
        subscription = Tables.Subscription.select_obj(self._conn, node_id = self.node_id, peer_id = self.node_id, message_id = message['message_id'])
        if subscription is None:
            subscription = {'peer_id': self.node_id,
                            'message_id': message['message_id'],
                            'local_is_subscribed': 1,
                            'local_center_node': self.node_id,
                            'local_center_distance': 1,
                            'remote_is_subscribed': 1,
                            'remote_center_node': self.node_id,
                            'remote_center_distance': 0}
        subscription['remote_is_subscribed'] = subscribed
        self.update_subscription(subscription)

    def delete_local_subscription(self, message):
        subscription = Tables.Subscription.select_obj(self._conn, node_id = self.node_id, peer_id = self.node_id, message_id = message['message_id'])
        if subscription is not None:
            self.delete_subscription(subscription)

    def post_text_message(self, content):
        return self.post_message({'content': content})

    def post_link_message(self, link_description, src_message, dst_message):
        return self.post_message({'content': link_description,
                                  'src_message_id': src_message['message_id'],
                                  'dst_message_id': dst_message['message_id']})


class LocalNode(ThreadSyncNode, IntrospectionNode, UINode):
    pass
