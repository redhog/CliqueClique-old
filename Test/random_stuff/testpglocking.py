#! /usr/bin/python

import pyPgSQL.PgSQL
def conn():
    return pyPgSQL.PgSQL.connect(
        user="cliqueclique",
        password="saltgurka",
        host="localhost",
        database="cliqueclique")

print "Insert"
c = conn()
cc = c.cursor()
cc.execute("delete from peer;")
cc.execute("insert into peer (node_id, peer_id) values(4711, 4712);")
cc.close()
c.commit()

print "Select"
c = conn()
cc = c.cursor()
cc.execute("select * from peer;")
print cc.fetchall()
cc.close()
c.commit()

print "Insert"
c = conn()
cc = c.cursor()
cc.execute("update peer set peer_id=4713;")
#cc.close()
#c.commit()

print "Select"
c = conn()
cc = c.cursor()
cc.execute("select * from peer;")
print cc.fetchall()
cc.close()
c.commit()
