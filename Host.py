from __future__ import with_statement

import contextlib, datetime, md5, os.path, Utils, Tables, Node, LocalNode, Config

class Host(object):
    def __init__(self, conn = None):
        self.node_cache = {}
        self.conn = conn or Config.database_engine()

    def _get_node(self, node_id):
        return LocalNode.LocalNode(self.conn, node_id, self)

    def get_node(self, node_id, cache = False):
        if not cache:
            return self._get_node(node_id)
        if node_id not in self.node_cache:
            self.node_cache[node_id] = self._get_node(node_id)
        return self.node_cache[node_id]
            
    def get_nodes(self):
        with Tables.Peer.select_objs_sql(self.conn, "node_id = peer_id") as objs:
            return [obj['node_id']
                    for obj in objs]

    def initialize(self):
        with contextlib.closing(self.conn.cursor()) as cur:
            for part in ("tables.sql", "views.sql"):
                with open(os.path.join(os.path.dirname(__file__), part)) as f:
                    cur.execute(f.read())
        self.conn.commit()

    def close(self):
        self.conn.close()
        for node in self.node_cache.values():
            node.close()
