from __future__ import with_statement

import datetime, md5, threading, operator, types
import Utils, Tables, Node, Visualizer
import symmetricjsonrpc

debug_sync = True
debug_sync_connect = True
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
        if subscription:
            if debug_sync:
                print "Sync: %s -> %s : %s, %s, delete:%s" % (Visualizer.VisualizerOperations._id2label(self.node_id),
                                                              Visualizer.VisualizerOperations._id2label(other.node_id),
                                                              subscription and Visualizer.VisualizerOperations._ids2labels(dict(subscription)),
                                                              message and Visualizer.VisualizerOperations._ids2labels(dict(message)),
                                                              delete_subscription)
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
        with Tables.Peer.select_objs(self._conn, self.node_id, *arg, **kw) as objs:
            return [obj['peer_id']
                    for obj in objs]

    def get_peer(self, peer_id):
        # Add XMLL-RPC connect interface here...
        return self.LocalPeerConnector(self.host.get_node(peer_id))

    class LocalPeerConnector(object):
        """Wrapper for Node that hides all methods that shouldn't be
        allowed to be accessed from remote hosts."""
        
        def __init__(self, local_peer):
            self._local_peer = local_peer
            
        def __getattribute__(self, name):
            if not hasattr(Node.Node, name):
                raise AttributeError("You can not use methods meant for the local node on peers, even when connected to them locally.", name)

            def wrap(local, member):
                def wrapper(*arg, **kw):
                    try:
                        return member(*arg, **kw)
                    except:
                        local.rollback()
                        raise
                    else:
                        local.commit()
                return wrapper

            local = object.__getattribute__(self, "_local_peer")
            member = getattr(local, name)
            if not isinstance(member, types.MethodType):
                return member
            return wrap(local, member)


class ThreadSyncNode(SyncNode):
    def __init__(self, *arg, **kw):
        self._sync_connected_peers = []
        self._sync_outbound_thread  = None
        self._sync_outbound_connection_manager_thread = None
        super(ThreadSyncNode, self).__init__(*arg, **kw)

    def commit(self):
        SyncNode.commit(self)
        self.host.signal_change()

    def sync_start(self):
        self._sync_outbound_thread = self.OutboundSyncThread(self, name="%s:outbound" % Visualizer.VisualizerOperations._id2label(self.node_id))
        self._sync_outbound_connection_manager_thread = self.OutboundConnectionManagerThread(self, name="%s:connmgr" % Visualizer.VisualizerOperations._id2label(self.node_id))
        
    def sync_stop(self):
        self._sync_outbound_thread.shutdown()
        self._sync_outbound_connection_manager_thread.shutdown()
        self._sync_outbound_thread  = None
        self._sync_outbound_connection_manager_thread = None

    def sync_add_peer(self, peer):
        self._sync_connected_peers.append(peer)
        self.host.signal_change()

    def sync_remove_peer(self, peer):
        self._sync_connected_peers.remove(peer)
        self.host.signal_change()

    class OutboundConnectionManagerThread(symmetricjsonrpc.Thread):
        def run_thread(self):
            while not self._shutdown:
                # Don't connect to localhost
                peer_ids = [peer.node_id for peer in self.subject._sync_connected_peers] + [self.subject.node_id]
                if len(peer_ids) == 1:
                    sql = 'peer_id != %s'
                else:
                    sql = 'peer_id not in (%s)' % (', '.join('%s' for peer_id in peer_ids),)
                non_connected_peers = self.subject.get_peers(_query_sql=(sql, peer_ids))
                for peer_id in non_connected_peers:
                    peer = self.subject.get_peer(peer_id)
                    if peer:
                        if debug_sync_connect: print "%s:connect:%s:success" % (self.getName(), Visualizer.VisualizerOperations._id2label(peer_id))
                        self.subject.sync_add_peer(peer)
                    else:
                        if debug_sync_connect: print "%s:connect:%s:failed" % (self.getName(), Visualizer.VisualizerOperations._id2label(peer_id))
                    if self._shutdown: return                
                self.subject.host.wait_for_change(reconnect_delay)

    class OutboundSyncThread(symmetricjsonrpc.Thread):
        def run_thread(self):
            while not self._shutdown:
                syncs = 0
                for peer in list(self.subject._sync_connected_peers): # Copy to avoid list changing under our feet...
                    try:
                        new_syncs = self.subject.sync_peer(peer)
                        syncs += new_syncs
                        if new_syncs: self.subject.commit()
                    except:
                        self.subject.rollback()
                        import traceback
                        traceback.print_exc()
                        self.subject.sync_remove_peer(peer)
                    if self._shutdown: return
                new_syncs = self.subject.sync_self()
                syncs += new_syncs
                if new_syncs: self.subject.commit()
                if self._shutdown: return
                if not syncs:
                    self.subject.host.wait_for_change(reconnect_delay)

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
        message['message_challenge_id'] = self.calculate_message_challenge_id(message)
        self._register_message(message)
        self.update_local_subscription(message)
        return message

    def update_local_subscription(self, message, subscribed = 1):
        subscription = Tables.Subscription.select_obj(self._conn, node_id = self.node_id, peer_id = self.node_id, message_id = message['message_id'])
        if subscription is None:
            subscription = {'peer_id': self.node_id,
                            'message_id': message['message_id'],
                            'local_is_subscribed': 1,
                            'local_center_node_is_subscribed': 1,
                            'local_center_node_id': self.node_id,
                            'local_center_distance': 1,
                            'remote_is_subscribed': 1,
                            'remote_center_node_is_subscribed': 1,
                            'remote_center_node_id': self.node_id,
                            'remote_center_distance': 0}
        subscription['remote_is_subscribed'] = subscribed
        subscription['remote_center_node_is_subscribed'] = subscribed
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
