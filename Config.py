import pyPgSQL.PgSQL, ThreadsafeConnection

def postgres_database_engine(**kw):
    def connect_to_postgres():
        conn= pyPgSQL.PgSQL.connect(**kw)
        def convert_data_out(data):
            if isinstance(data, pyPgSQL.PgSQL.PgNumeric):
                if data.getScale() == 0:
                    data = int(data)
                else:
                    # We probably lose some precission here...
                    data = float(data)
            return data
        conn.__dict__["convert_data_out"] = convert_data_out
        return conn
    return ThreadsafeConnection.ThreadsafeConnection(connect_to_postgres)
 
def database_engine():
    return postgres_database_engine(
        user="cliqueclique",
        password="saltgurka",
        host="localhost",
        database="cliqueclique")
