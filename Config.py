#import sqlite3
#database_engine = sqlite3.connect
#database_arguments = (("test.db",), {})

import pyPgSQL.PgSQL
database_engine = pyPgSQL.PgSQL.connect
database_arguments = ((), {'user':"cliqueclique", 'password':"saltgurka", 'host':"localhost", 'database':"cliqueclique"})
