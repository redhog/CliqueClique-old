from __future__ import with_statement

import Node, Tables

debug_message_expr = False

class ExprNode(Node.Node):
    def get_message_by_expr(self, expr):
        with self.get_messages_by_expr(expr) as msgs:
            for msg in msgs:
                return msg
            return None

    def get_messages_by_expr(self, expr):
        if debug_message_expr: print "get_messages_by_expr(%s)" % (expr,)
        froms, wheres, params = self._message_expr_to_sql(
            expr, "message.message_id", {"alias": 0, "vars": {}})
        return Tables.Message.select_objs(
            self._conn, self.node_id, _query_sql=(froms, ' and '.join(wheres), params))

    def _message_expr_to_sql(self, expr, prev, info): 
        data = {"alias_id": info['alias'],
                "node_id": self.node_id,
                "prev": prev,
                "param": Tables.Message._paramstyle_from_conn(self._conn)}
        if not expr:
            return self._message_expr_to_sql(['all'], prev, info)
        elif isinstance(expr, dict):
            return self._message_expr_to_sql(['id', expr['message_id']], prev, info)
        else:
            return getattr(self, "_message_expr_to_sql_" + expr[0])(expr, prev, info, data)

    def _message_expr_to_sql_all(self, expr, prev, info, data):
        return ([], [], [])

    def _message_expr_to_sql_var(self, expr, prev, info, data):
        if expr[1] in info['vars']:
            return [], ["%s = %s" % (prev, info['vars'][expr[1]])], []
        else:
            info['vars'][expr[1]] = prev
            return [], [], []
        
    def _message_expr_to_sql_ignore(self, expr, prev, info, data):
        info['alias'] += 1
        froms, wheres, params = self._message_expr_to_sql(expr[1], "a%(alias_id)s.message_id" % data, info)
        froms.append("message as a%(alias_id)s" % data)
        wheres.append("a%(alias_id)s.node_id = %(param)s" % data)
        params.append(self.node_id)
        return froms, wheres, params

    def _message_expr_to_sqlhelper_sequence(self, exprs, prevs, info): 
        froms = []
        wheres = []
        params = []
        for arg, prev in zip(exprs, prevs):
            froms1, wheres1, params1 = self._message_expr_to_sql(arg, prev, info)
            froms.extend(froms1)
            wheres.extend(wheres1)
            params.extend(params1)
        return froms, wheres, params

    def _message_expr_to_sql_and(self, expr, prev, info, data): 
        return self._message_expr_to_sqlhelper_sequence(expr[1:], [prev] * len(expr[1:]), info)

    def _message_expr_to_sql_or(self, expr, prev, info, data): 
        froms, wheres, params = self._message_expr_to_sqlhelper_sequence(expr[1:], [prev] * len(expr[1:]), info)
        wheres = ['(%s)' % (' or '.join(wheres),)]
        return froms, wheres, params

    def _message_expr_to_sql_inv(self, expr, prev, info, data):
        info['alias'] += 1
        return self._message_expr_to_sql(
            ["and",
             ["var", data['alias_id']],
             ["ignore",
              ["and",
               expr[1:-1] + [["var", data['alias_id']]],
               expr[-1]]]],
            prev, info)

    def _message_expr_to_sql_id(self, expr, prev, info, data): 
        return [], ["%(prev)s = %(param)s" % data], [expr[1]]

    def _message_expr_to_sql_content(self, expr, prev, info, data): 
        info['alias'] += 1

        froms = ["message as a%(alias_id)s" % data]
        wheres = ["""(    a%(alias_id)s.node_id = %(node_id)s
                      and a%(alias_id)s.content = %(param)s
                      and a%(alias_id)s.message_id = %(prev)s)""" % data]
        params = [expr[1]]
        return froms, wheres, params

    def _message_expr_to_sql_anno(self, expr, prev, info, data): 
        info['alias'] += 1

        froms = ["annotation as a%(alias_id)s" % data]
        wheres = ["""(    a%(alias_id)s.node_id = %(node_id)s
                      and a%(alias_id)s.name = %(param)s
                      and a%(alias_id)s.value = %(param)s
                      and a%(alias_id)s.message_id = %(prev)s
                      and a%(alias_id)s.peer_id is null)""" % data]
        params = [expr[1], expr[2]]
        return froms, wheres, params

    def _message_expr_to_sql_linksto(self, expr, prev, info, data): 
        info['alias'] += 1
        froms, wheres, params = self._message_expr_to_sql(
            expr[1],
            "a%(alias_id)s.dst_message_id" % data,
            info)
        froms.append("message_link as a%(alias_id)s" % data)
        wheres.append("""(    a%(alias_id)s.node_id = %(node_id)s
                          and a%(alias_id)s.src_message_id = %(prev)s)""" % data)
        return froms, wheres, params
    
    def _message_expr_to_sql_linkedfrom(self, expr, prev, info, data): 
        return self._message_expr_to_sql(
            ["inv", "linksto", expr[1]],
            prev, info)

    def _message_expr_to_sql_linkstovia(self, expr, prev, info, data): 
        info['alias'] += 2
        froms, wheres, params = self._message_expr_to_sqlhelper_sequence(
            expr[1:],
            ["a%(alias_id)s.message_id" % data,
             "a%(alias_id)s.dst_message_id" % data],
            info)
        froms.append("message as a%(alias_id)s" % data)
        wheres.append("""(    a%(alias_id)s.node_id = %(node_id)s
                          and a%(alias_id)s.src_message_id = %(prev)s)""" % data)
        return froms, wheres, params

    def _message_expr_to_sql_linkedfromvia(self, expr, prev, info, data): 
        return self._message_expr_to_sql(
            ["inv", "linkstovia", expr[1], expr[2]],
            prev, info)

    def _message_expr_to_sql_system(self, expr, prev, info, data): 
         return self._message_expr_to_sql(
             ["anno", "global_attribute_cache", "/system/%s" % (expr[1],)],
             prev, info)

    def _message_expr_to_sql_usagelink(self, expr, prev, info, data):
        return self._message_expr_to_sql(
            ["linkstovia", [], ["system", "usage"]],
            prev, info)
        
    def _message_expr_to_sql_usageis(self, expr, prev, info, data): 
        return self._message_expr_to_sql(
            ["linkstovia", ["usagelink"], expr[1]],
            prev, info)

    def _message_expr_to_sql_isusage(self, expr, prev, info, data): 
        return self._message_expr_to_sql(
            ["inv", "usageis", expr[1]],
            prev, info)

    def _message_expr_to_sql_typelink(self, expr, prev, info, data):
        return self._message_expr_to_sql(
            ["usageis", ["system", "type"]],
            prev, info)

    def _message_expr_to_sql_typeis(self, expr, prev, info, data): 
        return self._message_expr_to_sql(
            ["linkstovia", ["typelink"], expr[1]],
            prev, info)

    def _message_expr_to_sql_istype(self, expr, prev, info, data): 
        return self._message_expr_to_sql(
            ["inv", "typeis", expr[1]],
            prev, info)

    def _message_expr_to_sql_subtypelink(self, expr, prev, info, data):
        return self._message_expr_to_sql(
            ["usageis", ["system", "subtype"]],
            prev, info)
    
    def _message_expr_to_sql_basetypeis(self, expr, prev, info, data): 
        return self._message_expr_to_sql(
            ["linkstovia", ["subtypelink"], expr[1]],
            prev, info)

    def _message_expr_to_sql_isbasetype(self, expr, prev, info, data): 
        return self._message_expr_to_sql(
            ["inv", "basetypeis", expr[1]],
            prev, info)
    
    def _message_expr_to_sql_nametreelink(self, expr, prev, info, data):
        return self._message_expr_to_sql(
            ["usageis", ["system", "nametreelink"]],
            prev, info)

    def _message_expr_to_sql_nametreelinks(self, expr, prev, info, data):
        return self._message_expr_to_sql(
            ["linkstovia", ["and", ["nametreelink"], expr[1]], expr[2]],
            prev, info)

    def _message_expr_to_sql_nametreelinked(self, expr, prev, info, data):
        return self._message_expr_to_sql(
            ["inv", "nametreelinks", expr[1], expr[2]],
            prev, info)

    def _message_expr_to_sql_nametreelookup(self, expr, prev, info, data):
        # nametreelookup name root
        info['alias'] += 1
        
        if isinstance(expr[2], dict) or expr[2][0] == 'id':
            froms = ["message as a%(alias_id)s" % data]
            wheres = ["""(    a%(alias_id)s.node_id = %(node_id)s
                          and a%(alias_id)s.content = 'nametreenode:' || %(param)s || ':' || %(param)s
                          and a%(alias_id)s.message_id = %(prev)s)""" % data]
            if isinstance(expr[2], dict):
                root = expr[2]['message_id']
            else:
                root = expr[2][1]
            params = [self.id2s(root), expr[1]]
        else:
            raise NotImplementedError("Not yet implemented")
            info['alias'] += 1
            data['root_alias_id'] = data['alias_id'] + 1

            froms, wheres, params = self._message_expr_to_sql(
                expr[2],
                "a%(root_alias_id)s.message_id" % data,
                info)

            froms.append("message as a%(root_alias_id)s" % data)
            froms.append("message as a%(alias_id)s" % data)

            wheres.append("""(    a%(root_alias_id)s.node_id = %(node_id)s
                              and a%(alias_id)s.node_id = %(node_id)s
                              and a%(alias_id)s.content = 'nametreenode:' || to_hex(a%(root_alias_id)s.message_id) || ':' || %(param)s
                              and a%(alias_id)s.message_id = %(prev)s)""" % data)
            params.append(expr[1])
        return froms, wheres, params
    
    def _message_expr_to_sql_nametreeleaflink(self, expr, prev, info, data):
        return self._message_expr_to_sql(
            ["usageis", ["system", "nametreeleaflink"]],
            prev, info)

    def _message_expr_to_sql_nametreeleaflinks(self, expr, prev, info, data):
        return self._message_expr_to_sql(
            ["linkstovia", ["and", ["nametreeleaflink"], expr[1]], expr[2]],
            prev, info)

    def _message_expr_to_sql_nametreeleaflinked(self, expr, prev, info, data):
        return self._message_expr_to_sql(
            ["inv", "nametreeleaflinks", expr[1], expr[2]],
            prev, info)
    
    def _message_expr_to_sql_nametreelookupentry(self, expr, prev, info, data):
        return self._message_expr_to_sql(["nametreeleaflinked", [], ["nametreelookup", expr[1], expr[2]]], prev, info)
