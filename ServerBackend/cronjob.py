import sqlite3
import csv
from datetime import datetime

dbpath = 'opt/sqlite/bcapp.sqlite'

def main():
    dataDump()
    removeEverything()

def dataDump():
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    ack = {}
    data = []

    curYear = datetime.now().year
    lastYear = curYear - 1

    curDate = str(curYear) + '-09-01'
    lastDate = str(lastYear) + '-09-01'

    cursor.execute("SELECT uniqueID, added, msgSent, stationAvailable, arrived, endTime, noShow, cancelled, flushedFromWaitlist FROM timestamps WHERE dateAdded > ? AND dateAdded < ?", (lastDate,curDate,))

    for row in cursor:
    	isItThere = "yes" if row[2] == 1 else "no"
    	data.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]])

    with open("dataDump.csv", "w") as csvFile:
    	 wr = csv.writer(csvFile)
	 wr.writerows(data)

    ack["result"] = 1

    conn.close()

def removeEverything():
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    ack = {}

    cursor.execute("DELETE FROM waitlist")
    cursor.execute("DELETE FROM people")

    conn.commit()

    ack["result"] = 1
    conn.close()

if __name__ == '__main__':
	main()