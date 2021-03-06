from __future__ import with_statement

import traceback, operator, socket, symmetricjsonrpc
import Utils, Tables, Node, Visualizer

debug_sync = True
debug_sync_connect = True
debug_sync_connect_details = False
reconnect_delay = 10.0

class HostedNode(Node.Node):
    def __init__(self, _conn, node_id, host, **kw):
        self.host = host
        Node.Node.__init__(self, _conn, node_id, **kw)

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

        subscription, message, delete_subscription = self.get_subscription_update(other.get_local_node()['node_id'])
        if subscription:
            if debug_sync:
                print "Sync: %s -> %s : %s, %s, delete:%s" % (Visualizer.VisualizerOperations._id2label(self.get_local_node()['node_id']),
                                                              Visualizer.VisualizerOperations._id2label(other.get_local_node()['node_id']),
                                                              subscription and Visualizer.VisualizerOperations._ids2labels(dict(subscription)),
                                                              message and Visualizer.VisualizerOperations._ids2labels(dict(message)),
                                                              delete_subscription)
            if delete_subscription:
                other.delete_subscription(subscription)
            else:
                # Yes, ignore result if syncing self, just pretend we did an update
                if self.get_local_node()['node_id'] != other.get_local_node()['node_id']:
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
            {'peer_id': other.get_local_node()['node_id'],
             'message_id': message['message_id']})
        self.update_local_subscription(message, 0)

    def get_peers(self, *arg, **kw):
        with Tables.Peer.select_objs(self._conn, self.get_local_node()['node_id'], *arg, **kw) as objs:
            return list(objs)

class ThreadSyncNode(SyncNode):
    def __init__(self, *arg, **kw):
        self._janitor_thread = None
        self._sync_thread  = None
        super(ThreadSyncNode, self).__init__(*arg, **kw)

    def commit(self):
        SyncNode.commit(self)
        self.host.signal_change()

    def sync_start(self):
        self._janitor_thread = self.Janitor(None, self, name="%s:Janitor" % Visualizer.VisualizerOperations._id2label(self.get_local_node()['node_id']))
        self._sync_thread = self.ConnectionManager.listen(
            self.get_local_node(), self, name="%s:ConnectionManager" % Visualizer.VisualizerOperations._id2label(self.get_local_node()['node_id']))
        
    def sync_stop(self):
        self._janitor_thread.shutdown()
        self._janitor_thread  = None
        self._sync_thread.shutdown()
        self._sync_thread  = None

    class Janitor(symmetricjsonrpc.Thread):
        def run_thread(self):
            node = self.parent
            while not self._shutdown:
                try:
                    syncs = node.sync_self()
                    if syncs: node.commit()
                    if self._shutdown: return
                    if not syncs:
                        node.host.wait_for_change(reconnect_delay)
                except:
                    node.rollback()
                    traceback.print_exc()
        
    class ConnectionManager(symmetricjsonrpc.RPCP2PNode):
        class Thread(symmetricjsonrpc.RPCP2PNode.Thread):
            class InboundConnection(symmetricjsonrpc.RPCP2PNode.Thread.InboundConnection):
                class Thread(symmetricjsonrpc.RPCP2PNode.Thread.InboundConnection.Thread):
                    class Request(symmetricjsonrpc.RPCP2PNode.Thread.InboundConnection.Thread.Request):
                        def dispatch_request(self, subject):
                            node = self.parent.parent.parent.parent.parent

                            if not hasattr(Node.Node, subject['method']):
                                raise AttributeError("Unknown or illegal method.", subject['method'])
                            try:
                                res = getattr(node, subject['method'])(*subject['params'])
                            except:
                                node.rollback()
                                raise
                            else:
                                node.commit()
                            return res

                        def dispatch_notification(self, subject):
                            self.dispatch_request(subject)

                        def dispatch_response(self, subject):
                            # We do not support callback-style responses
                            assert False
                    
                    def run_parent(self):
                        """Sync connected peers"""

                        connmgr = self.parent.parent.parent
                        node = connmgr.parent

                        peer_id = self.get_local_node()['peer_id']
                        connmgr.sync_add_peer(peer_id, self.parent)

                        try:
                            try:
                                while not self._shutdown:
                                    syncs = node.sync_peer(self)
                                    if syncs: node.commit()
                                    if self._shutdown: return
                                    if not syncs:
                                        node.host.wait_for_change(reconnect_delay)
                            except:
                                node.rollback()
                                raise
                        finally:
                            connmgr.sync_remove_peer(peer_id)

                @classmethod
                def connect_to_peer(cls, peer, *arg, **kw):
                    return cls(cls._connect_to_peer(peer), *arg, **kw)

                @classmethod
                def _connect_to_peer(cls, peer):
                    parts = peer['last_seen_address'].split('/')
                    conn = None
                    for part in parts:
                        addr_type, args = part.split(':', 1)
                        args = args and args.split(':') or []
                        conn = getattr(cls, "_connect_to_peer_%s" % (addr_type,))(conn, *args)
                    return conn

                @classmethod
                def _connect_to_peer_tcp(self, conn, host, port):
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((host, int(port)))
                    return s

            def run_parent(self):
                """Connect to unconnected peers"""
                node = self.parent.parent
                
                while not self._shutdown:
                     # Don't connect to localhost
                     peer_ids = self.parent.sync_connected_peers.keys() + [node.get_local_node()['node_id']]
                     if len(peer_ids) == 1:
                         sql = 'peer_id != %s'
                     else:
                         sql = 'peer_id not in (%s)' % (', '.join('%s' for peer_id in peer_ids),)
                     non_connected_peers = node.get_peers(_query_sql=([], sql, peer_ids))
                     for peer in non_connected_peers:
                         try:
                             client = self.InboundConnection.connect_to_peer(
                                 peer, self, name="%s:client:%s" % (self.getName(), Visualizer.VisualizerOperations._id2label(peer['peer_id'])))
                             if debug_sync_connect:
                                 print "%s:connect:%s@%s:success" % (self.getName(), Visualizer.VisualizerOperations._id2label(peer['peer_id']), peer['last_seen_address'])
                         except:
                             if debug_sync_connect:
                                 print "%s:connect:%s@%s:failed:" % (self.getName(), Visualizer.VisualizerOperations._id2label(peer['peer_id']), peer['last_seen_address'])
                                 if debug_sync_connect_details:
                                     traceback.print_exc()
                         if self._shutdown: return          
                     node.host.wait_for_change(reconnect_delay)

        def _init(self, *arg, **kw):
            self.sync_connected_peers = {}
            symmetricjsonrpc.RPCP2PNode._init(self, *arg, **kw)

        def sync_add_peer(self, peer, thread):
            node = self.parent
            self.sync_connected_peers[peer] = thread
            node.host.signal_change()

        def sync_remove_peer(self, peer):
            node = self.parent
            del self.sync_connected_peers[peer]
            node.host.signal_change()

        @classmethod
        def listen(cls, node, *arg, **kw):
            return cls(cls._listen(node), *arg, **kw)

        @classmethod
        def _listen(cls, node):
            parts = node['last_seen_address'].split('/')
            conn = None
            for part in parts:
                addr_type, args = part.split(':', 1)
                args = args and args.split(':') or []
                conn = getattr(cls, "_listen_%s" % (addr_type,))(conn, *args)
            return conn

        @classmethod
        def _listen_tcp(cls, conn, host, port):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, int(port)))
            s.listen(1)
            return s
