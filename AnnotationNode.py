from __future__ import with_statement

import Tables, Node

class AnnotationNode(Node.Node):
    def set_annotation(self, name, value, message = None, peer = None):
        Tables.Annotation.create_or_update(
            self._conn,
            {'node_id': self.node_id,
             'name': name,
             'message_id': message and message['message_id'] or None,
             'peer_id': peer and peer['peer_id'] or None,
             'value': value})
        
    def get_annotation(self, name, message = None, peer = None):
        return Tables.Annotation.select_obj(
            self._conn, self.node_id,
            name,
            message and message['message_id'] or None,
            peer and peer['peer_id'] or None)['value']
