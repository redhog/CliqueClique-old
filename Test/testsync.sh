rm test.db; cat tables.sql views.sql | sqlite3 test.db; ./testsync.py --nodes=2 --poster=1
