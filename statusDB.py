import sqlite3


class StatusDB:
	def __init__(self):
		self.conn = sqlite3.connect('./status.db')
		
		self.conn.execute('''CREATE TABLE IF NOT EXISTS status
		             (runId int primary key not null unique,
			      status varchar(20) not null,
			      message text,
  			      pbsId int,
			      jobType text)''')
		self.conn.commit()
		print "Should have created table"

	def updatePBSId(self,runId,runType,pbsId):
		try:
			c = self.conn.cursor()
			c.execute('SELECT * from status where runId = "' + str(runId) + '"')
			rows = c.fetchall()
			if len(rows) > 0:
				SQLString = 'UPDATE Status SET jobType= "%s", pbsId = "%s" where runId = %s'%(runType,str(pbsId),str(runId))
				c.execute(SQLString)
				self.conn.commit()
				return True
		except Exception as e:
			print "Problem Updating Status " + str(e)
			return False

	def updateEntry(self,runId,status = 'staging', message = 'Job is gathering inputs from database'):
		try:
			c = self.conn.cursor()
			c.execute('SELECT * from status where runId = "' + str(runId) + '"')
			rows = c.fetchall()
			print "Number of Rows = " + str(len(rows))
			if len(rows) > 0:
				print "Updating"
				SQLString = 'UPDATE Status SET status = "%s", message = "%s" where runId = %s'%(status,message,runId)
				c.execute(SQLString)
				self.conn.commit()
				print "Committing"
				return True
			else:
				print "Inserting"
				SQLString = 'INSERT INTO status VALUES ("%s","%s","%s",-1,"")'\
					    %(runId, status, message)
				c.execute(SQLString)
				self.conn.commit()
				return True
		except Exception as e:
			print "Problem Updating Status " + str(e)
			return False
		

	def getPBSId(self,runId):
		try:
			c = self.conn.cursor()
			SQLString = 'SELECT * from status where runId = "%s"'%str(runId)
			c.execute(SQLString)
			rows = c.fetchall()
			if len(rows) == 0:
				return "-1"
			elif rows[0][4] == "pbs":	
				return(rows[0][3])
			else:
				return None
		except Exception as e:
                        print "There was a problem " + str(e)
                        return False

	def getEntry(self,runId):
		try:
			c = self.conn.cursor()
			SQLString = 'SELECT * from status where runId = "%s"'%str(runId)
			c.execute(SQLString)
			rows = c.fetchall()
			if len(rows) == 0:
				return ("UNKNOWN","Unable to find status for runID %s in database"%str(runId))
			else:
				
				return (rows[0][1],rows[0][2])
		except Exception as e:
			print "There was a problem " + str(e)
			return False
