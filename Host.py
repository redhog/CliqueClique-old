from __future__ import with_statement

import contextlib, datetime, md5, os.path, Utils, Tables, Node, LocalNode, Config, threading

debug_change_wait = False
debug_change_wait_details = False

class Host(object):
    def __init__(self, engine = None):
        self._conn_factory = engine or Config.database_engine
        self._node_cache = {}
        self._conn = self._conn_factory()
        self.changes = threading.Condition()

    def _get_node(self, node_id, **kw):
        return LocalNode.LocalNode(self._conn, node_id, self, **kw)

    def get_node(self, node_id, cache = False, **kw):
        if not cache:
            return self._get_node(node_id, **kw)
        if node_id not in self._node_cache:
            self._node_cache[node_id] = self._get_node(node_id, **kw)
        return self._node_cache[node_id]
            
    def get_nodes(self):
        with Tables.Peer.select_objs_sql(self._conn, "node_id = peer_id") as objs:
            return [obj['node_id']
                    for obj in objs]

    def initialize(self):
        self._node_cache = {}
        with contextlib.closing(self._conn.cursor()) as cur:
            for part in ("tables.sql", "views.sql"):
                with open(os.path.join(os.path.dirname(__file__), part)) as f:
                    cur.execute(f.read())
        self._conn.commit()

    def commit(self):
        self._conn.commit()
        for node in self._node_cache.values():
            node.commit()

    def rollback(self):
        self._conn.rollback()
        for node in self._node_cache.values():
            node.rollback()

    def close(self):
        self._conn.close()
        for node in self._node_cache.values():
            node.close()

    def wait_for_change(self, timeout = None):
        if debug_change_wait:
            name = ['wait', 'aquire'][debug_change_wait_details]
            print "%s:wait_for_change:%s" % (threading.currentThread().getName(), name)
        with self.changes:
            if debug_change_wait and debug_change_wait_details: print "%s:wait_for_change:wait" % threading.currentThread().getName() 
            self.changes.wait(timeout)
            if debug_change_wait and debug_change_wait_details: print "%s:wait_for_change:release" % threading.currentThread().getName() 

    def signal_change(self):
        if debug_change_wait:
            name = ['notify', 'aquire'][debug_change_wait_details]
            print "%s:signal_change:%s" % (threading.currentThread().getName(), name)
        with self.changes:
            if debug_change_wait and debug_change_wait_details: print "%s:signal_change:notify" % threading.currentThread().getName() 
            self.changes.notifyAll()
            if debug_change_wait and debug_change_wait_details: print "%s:signal_change:release" % threading.currentThread().getName() 
