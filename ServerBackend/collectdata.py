import sqlite3
import csv
import argparse

dbpath = 'opt/sqlite/bcapp.sqlite'

def main():
    parser = argparse.ArgumentParser(description = "Obtain a log of data from one year to another (fiscal year starting Sep. 1)")
    parser.add_argument("yearOne", help = "Starting year")
    parser.add_argument("yearTwo", help = "Ending year")
    args = parser.parse_args()
    dataDump(args.yearOne, args.yearTwo)

def dataDump(yearOne, yearTwo):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    ack = {}
    data = []

    curDate = yearTwo + '-09-01'
    lastDate = yearOne + '-09-01'

    cursor.execute("SELECT uniqueID, added, msgSent, stationAvailable, arrived, endTime, noShow, cancelled, flushedFromWaitlist FROM timestamps WHERE dateAdded > ? AND dateAdded < ?", (lastDate,curDate,))

    for row in cursor:
    	isItThere = "yes" if row[2] == 1 else "no"
    	data.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]])

    with open("dataDump.csv", "w") as csvFile:
    	 wr = csv.writer(csvFile)
	 wr.writerows(data)

    ack["result"] = 1

    conn.close()

if __name__ == '__main__':
	main()