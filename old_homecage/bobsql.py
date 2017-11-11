#!/usr/bin/env python
import MySQLdb
import sys, time, datetime
import multiprocessing #from: http://pymotw.com/2/multiprocessing/basics.html

def connect_local():
    """connect when on bluehost and return (db,c)"""
    try:
        db = connect('localhost')
        c = open(db)
        return (db, c)
    except:
        print 'bobsql.connect_local() error'

def connect2():
    """return (db, c)"""
    try:
	db = connect()
	c = open(db)
	return (db, c)
    except:
	print 'bobsql.connect2() error'

def connect(*host):
    """returns db"""
    if (len(host)==0):
	host = ['box873.bluehost.com'] #ow localhost
    #user = 'robertcu_monitor'
    #pw = 'poetry7d'
    #db = 'robertcu_temps' #database
    try:
        db = MySQLdb.connect(host = host[0], 
	    user = "robertcu_monitor", 
	    passwd = "poetry7d", 
	    db = "robertcu_running1")
	return db
    except MySQLdb.Error, e:
	print "bobsql.connect() error %d: %s" % (e.args[0], e.args[1])
	#print 'bob is calling sys.exit(1)'
	#sys.exit(1)
	return []

def open(db):
    """returns cursor"""
    try:
	cursor = db.cursor(MySQLdb.cursors.DictCursor) #open using dict
	return cursor
    except MySQLdb.Error, e:
        print "bobsql.open() error %d: %s" % (e.args[0], e.args[1])
        return []

def close(db, cursor):
    try:
	cursor.close()
	db.close()
    except MySQLdb.Error, e:
        print 'bobsql.close() error %d: %s' % (e.args[0], e.args[1])

def printdb(cursor):
    try:
	cursor.execute ("SELECT * FROM running1")
	#retrieve headers
	num_fields = len(cursor.description)
	field_names = [i[0] for i in cursor.description]
	#
	print '============================================================='
	#print field_names, trailing ','  in print does not print new line
	for x in field_names:
	    print x, '\t',
	print ''

	#fetch all using a dict
	result_set = cursor.fetchall()
	for row in result_set:
	    print "%s, %s, %s, %s, %s, %s" % (row["tdate"], row["ttime"],
	        row["seconds"], 
	        row["event"], 
	        row["val1"], 
	        row["val2"])
    except MySQLdb.Error, e:
	print 'bobsql.printdb() error'

def append_test(db, c):
    """test append_one()"""
    now = datetime.datetime.now()
    dateStr = now.strftime('%Y%m%d')
    timeStr = now.strftime('%H%M%S')
    mySeconds = time.time()
    ts = (dateStr, timeStr, mySeconds) #mimics ts from home.py
    append_one(db, c, ts, 'test1', 22, 33)

def append_one(db, cursor, ts, theEvent, val1, val2):
    """1"""
    try:
	cursor.execute(
	    "INSERT INTO running1 VALUES (%s,%s,%s,%s,%s,%s)",
	    (ts[0], ts[1], ts[2], theEvent, val1, val2))
	db.commit()
    except:
        print 'bobsql.append_one() error in INSERT INTO'
        db.rollback()

def append_many(db, c, log):
    """append many records to sql, log is coming from home.log['b']"""
    try:
	#print 'in append_many'
	c.executemany(
	    "INSERT INTO running1 VALUES (%s, %s, %s, %s, %s, %s)",
	    log)	    
	db.commit()
    except:
	print 'ERROR: bobsql.append_many()'
	db.rollback()

def append_many_worker(log, logNumber):
    try:
	startTime = time.time()
	print '   -->> STARTING append_many_worker()', logNumber
	db, c = connect2()
	append_many(db, c, log)
	close(db, c)
        stopTime = time.time()
	ostr = '   -->> FINISHED append_many_worker()'
	ostr += ' in ' + str(stopTime-startTime) + ' seconds' 
	ostr += ', logNumber ' + str(logNumber)
	print ostr
    except:
	print 'ERROR: bobsql.append_many_worker()'
    return

def append_many2(log, logNumber):
    """try and multithread"""
    try:
	p = multiprocessing.Process(
	    target=append_many_worker,
	    args=(log,logNumber))
	p.start()
    except:
        print 'ERROR: bobsql.append_many2()'

