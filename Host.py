from __future__ import with_statement

import contextlib, datetime, md5, os.path, Utils, Tables, Node, LocalNode, Config, threading

class Host(object):
    def __init__(self, engine = None):
        self._conn_factory = engine or Config.database_engine
        self._node_cache = {}
        self._conn = self._conn_factory()
        self.changes = threading.Condition()

    def _get_node(self, node_id):
        return LocalNode.LocalNode(self._conn, node_id, self)

    def get_node(self, node_id, cache = False):
        if not cache:
            return self._get_node(node_id)
        if node_id not in self._node_cache:
            self._node_cache[node_id] = self._get_node(node_id)
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
