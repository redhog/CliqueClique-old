from __future__ import with_statement

import Node, AnnotationNode, SyncNode, ExprNode, SubscriptionNode, PostingNode, IntrospectionNode, Tables

class InitializationNode(SyncNode.ThreadSyncNode, IntrospectionNode.IntrospectionNode, PostingNode.PostingNode):
     def _set_system_attribute(self, name, message):
          self.set_annotation("global_attribute_cache", "/system/%s" % name, message)
          return message

     def _post_system_message(self, name):
          return self._set_system_attribute(name, self.post_text_message(name))

     def _post_typed_system_message(self, name, type):
          return self._set_system_attribute(name, self.post_typed_text_message(name, type))

     def _post_type_system_message(self, name, parent):
          res = self._post_typed_system_message(name, self.get_message_by_expr(["system", "type"]))
          self.post_subtypelink_message(res, parent)
          return res

     def _initialize(self, **kw):
          do_typesystem = kw.pop('typesystem', True)
          
          Node.Node._initialize(self, **kw)

          if not do_typesystem:
              return

          self._post_system_message('usage')
          self._post_system_message('type')
          self._post_system_message('subtype')

          self.post_typelink_message(self.get_message_by_expr(["system", "type"]),
                                     self.get_message_by_expr(["system", "type"]))
          self.post_typelink_message(self.get_message_by_expr(["system", "usage"]),
                                     self.get_message_by_expr(["system", "type"]))
          self.post_typelink_message(self.get_message_by_expr(["system", "subtype"]),
                                     self.get_message_by_expr(["system", "type"]))

          self.post_subtypelink_message(self.get_message_by_expr(["system", "usage"]),
                                        self.get_message_by_expr(["system", "type"]))
          self.post_subtypelink_message(self.get_message_by_expr(["system", "subtype"]),
                                        self.get_message_by_expr(["system", "usage"]))

          self._post_type_system_message('nametreelink', self.get_message_by_expr(["system", "usage"]))
          self._post_type_system_message('nametreenode', self.get_message_by_expr(["system", "type"]))
          self._post_type_system_message('nametreeleaflink', self.get_message_by_expr(["system", "usage"]))

          self._post_type_system_message('text', self.get_message_by_expr(["system", "type"]))
          self._post_type_system_message('xml', self.get_message_by_expr(["system", "text"]))
          self._post_type_system_message('xhtml', self.get_message_by_expr(["system", "xml"]))
          self._post_type_system_message('css', self.get_message_by_expr(["system", "text"]))

          self._set_system_attribute('rootdir', self.post_nametreeroot_message('root'))
