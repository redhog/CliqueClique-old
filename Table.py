from __future__ import with_statement
import contextlib, sys



class Table(object):
    table_name = None
    id_cols = ()
    cols = None

    paramstyles = {'pyformat': '%s', 'qmark': '?'}

    @classmethod
    def _paramstyle_from_conn(cls, conn):
        return cls.paramstyles[sys.modules[conn.__module__].paramstyle]

    class _SelectDicts(object):
        def __init__(self, conn, *arg, **kw):
            self.conn = conn
            self.arg = arg
            self.kw = kw
            self.cols = None

        def __enter__(self):
            self.cur = self.conn.cursor()
            try:
                self.cur.execute(*self.arg, **self.kw)
            except:
                self.__exit__(*sys.exc_info())
                raise
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.cur.close()
            if exc_value is not None:
                exc_value.args = exc_value.args + (self.arg, self.kw)

        def __iter__(self):
            return self

        def next(self):
            if not hasattr(self, "cur"): raise Exception("This is not an iterator but a context manager. Please use a with-statement, and iterate over the result variable.")
            row = self.cur.fetchone()
            if row is None: raise StopIteration
            if self.cols is None: self.cols = [dsc[0] for dsc in self.cur.description]
            return dict(zip(self.cols, row))
    
    @classmethod
    def _select_dicts(cls, conn, *arg, **kw):
        return cls._SelectDicts(conn, *arg, **kw)
                
    @classmethod
    def _select_dict(cls, conn, *arg, **kw):
        with cls._select_dicts(conn, *arg, **kw) as results:
            for result in results:
                return result
        return None

    @classmethod
    def _get_query(cls, conn, *arg, **kw):
        kw.update(dict(zip(cls.id_cols, arg)))
        extra_sql, extra_params = kw.pop('_query_sql', ("1 = 1", []))
        if not kw:
            return extra_sql, extra_params
        query_keys = kw.keys()
        query_sql = ' and '.join("%s = %s" % (query_key, cls._paramstyle_from_conn(conn)) for query_key in query_keys)
        query_params = [kw[query_key] for query_key in query_keys]
        return extra_sql + " and " + query_sql, extra_params + query_params

    @classmethod
    def select_objs(cls, conn, *arg, **kw):
        cols = "*"
        if cls.cols:
            cols = ', '.join(cls.cols)
        query_sql, query_params = cls._get_query(conn, *arg, **kw)
        return cls._select_dicts(conn, "select %s from %s where %s" % (cols, cls.table_name, query_sql),
                                 query_params)
    
    @classmethod
    def select_obj(cls, conn, *arg, **query):
        with cls.select_objs(conn, *arg, **query) as results:
            for result in results:
                return result
            return None

    @classmethod
    def select_objs_sql(cls, conn, query_sql, query_params = ()):
        return cls.select_objs(conn, _query_sql = (query_sql, query_params))
    
    @classmethod
    def select_obj_sql(cls, conn, query_sql, query_params = ()):
        return cls.select_obj(conn, _query_sql = (query_sql, query_params))
    
    @classmethod
    def create_or_update(cls, conn, obj):
        id_col_values = [obj[col] for col in cls.id_cols]
        obj_cols = obj.keys()
        obj_non_id_cols = [key for key in obj_cols
                           if key not in cls.id_cols]

        existing = cls.select_obj(conn, *id_col_values)
        
        with contextlib.closing(conn.cursor()) as cur:
            if existing:
                query_sql, query_params = cls._get_query(conn, *id_col_values)
                cur.execute("""update %s set %s where %s""" % (cls.table_name,
                                                               ', '.join("%s = %s" % (col, cls._paramstyle_from_conn(conn)) for col in obj_non_id_cols),
                                                               query_sql),
                            [obj[col] for col in obj_non_id_cols] + query_params)
            else:
                query = """insert into %s (%s) values (%s)""" % (cls.table_name,
                                                                     ', '.join(obj_cols),
                                                                     ', '.join(cls._paramstyle_from_conn(conn) for col in obj_cols))
                cur.execute(query,
                            [obj[col] for col in obj_cols])

    @classmethod
    def delete(cls, conn, *arg, **kw):
        query_sql, query_params = cls._get_query(conn, *arg, **kw)
        with contextlib.closing(conn.cursor()) as cur:
            cur.execute("delete from %s where %s" % (cls.table_name, query_sql),
                        query_params)
