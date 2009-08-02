#import sqlite3
#database_engine = sqlite3.connect
#database_arguments = (("test.db",), {})

import pyPgSQL.PgSQL, ThreadsafeConnection

database_engine = lambda : ThreadsafeConnection.ThreadsafeConnection(
    lambda: pyPgSQL.PgSQL.connect(
        user="cliqueclique",
        password="saltgurka",
        host="localhost",
        database="cliqueclique"))
