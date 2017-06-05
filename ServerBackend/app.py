import bottle
import json
from json import dumps
from bottle import route, request, run, template, redirect, error, static_file, get, response, post
import sqlite3
from datetime import datetime, timedelta
from twilio.rest import TwilioRestClient
import twilio.twiml
import csv

# ... build or import your bottle application here ...
# Do NOT use bottle.run() with mod_wsgi
application = bottle.default_app()

# Twilio setup
# Twilio account SID & auth token; find them on http://www.twilio.com/user/account
ACCOUNT_SID = "################################"
AUTH_TOKEN = "##############################"
client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
serverPhoneNum = "#############"

# Datetime string formats
datetimeFormat = "%Y/%m/%d %I:%M %p"
dateFormat = "%Y-%m-%d"

# ############### Test API's ############### #

@application.route('/')
def test():
    test = {}
    curTime = datetime.now().strftime("%Y/%m/%d %I:%M %p")
    test["text"] = "Test successful"
    test["time"] = curTime
    return json.dumps(test)

@application.route('/removeEverything')
def removeEverything():
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    ack = {}

    cursor.execute("DELETE FROM people")
    cursor.execute("DELETE FROM waitlist")
    cursor.execute("DELETE FROM timestamps")

    conn.commit()

    ack["result"] = 1
    conn.close()
    return dumps(ack)

# ############### Waitlist API's ############### #

@application.post('/addNewEntry')
def addNewEntry():
    uniqueID = request.forms.get("uniqueID")
    phoneNum = request.forms.get("phoneNum")
    firstName = request.forms.get("firstName")
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    ack = {}
    newCount = 0
    curTime = ""

    try:
        curTime = datetime.now().strftime(datetimeFormat)
        curDate = datetime.now().strftime(dateFormat)
        cursor.execute("INSERT INTO people VALUES(?,?,?,?)", (uniqueID, firstName, phoneNum, curTime,))

        cursor.execute("SELECT count(*) FROM waitlist")
        count = cursor.fetchone()
        newCount = count[0] + 1
        cursor.execute("INSERT INTO waitlist VALUES(?,?)", (uniqueID, newCount,))

        cursor.execute("INSERT INTO timestamps(uniqueID,added,dateAdded) VALUES(?,?,?)", (uniqueID, curTime, curDate,))
    except sqlite3.IntegrityError:
        conn.rollback()
        ack["result"] = 0
        conn.close()
        return dumps(ack)

    try:
        if phoneNum != "0":
            phoneNum = "+1" + phoneNum
            body = "Hey " + uniqueID + "!\n\nYou have been added to the Bikechain Waitlist. You can check the number of people ahead of you on the waitlist using Bikechain's web app here:\n\n(Temporarily unavailable)"

            sendMessage(phoneNum,body)
            sentComplete = True
            cursor.execute("UPDATE timestamps SET msgSent = ? WHERE uniqueID = ?", (sentComplete, uniqueID,))
    except TwilioRestException:
        conn.rollback()
        ack["result"] = -1
        conn.close()
        return dumps(ack)

    ack["result"] = 1
    ack["position"] = newCount

    conn.commit()
    conn.close()
    return dumps(ack)

@application.post('/reRegister')
def reRegister():
    uniqueID = request.forms.get("uniqueID")
    phoneNum = request.forms.get("phoneNum")
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    ack = {}
    newCount = 0

    addTime = ""

    cursor.execute("SELECT * FROM people WHERE uniqueID = ?", (uniqueID,))
    isThere = cursor.fetchone()

    cursor.execute("SELECT * FROM waitlist WHERE uniqueID = ?", (uniqueID,))
    isInList = cursor.fetchone()

    if isThere != None and isInList == None:
        cursor.execute("UPDATE people SET phoneNum = ? WHERE uniqueID = ?", (phoneNum, uniqueID,))
        curTime = datetime.now().strftime(datetimeFormat)
        curDate = datetime.now().strftime(dateFormat)
        cursor.execute("UPDATE people SET latestTs = ? WHERE uniqueID = ?", (curTime, uniqueID,))

        cursor.execute("SELECT count(*) FROM waitlist")
        count = cursor.fetchone()
        newCount = count[0] + 1
        cursor.execute("INSERT INTO waitlist VALUES(?,?)", (uniqueID, newCount,))

        cursor.execute("INSERT INTO timestamps(uniqueID,added,dateAdded,msgSent) VALUES(?,?,?)", (uniqueID, curTime, curDate,))
        addTime = curTime
    else:
        ack["result"] = 0
        conn.close()
        return dumps(ack)
    
    try:
        if phoneNum != "0":
            phoneNum = "+1" + phoneNum
            body = "Hey " + uniqueID + "!\n\nYou have been added to the Bikechain Waitlist. You can check the number of people ahead of you on the waitlist using \
Bikechain's web app here:\n\n(Temporarily unavailable)"

            sendMessage(phoneNum,body)
            sentComplete = True
            cursor.execute("UPDATE timestamps SET msgSent = ? WHERE uniqueID = ? AND added = ?", (sentComplete, uniqueID, addTime))
    except TwilioRestException:
        conn.rollback()
        ack["result"] = -1
        conn.close()
        return dumps(ack)
    
    ack["result"] = 1
    ack["position"] = newCount
    
    conn.commit()
    conn.close()
    return dumps(ack)


@application.post('/delete')
def delete():
    uniqueID = request.forms.get("uniqueID")
    state = request.forms.get("state")
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    ack = {}

    cursor.execute("SELECT position FROM waitlist WHERE uniqueID = ?", (uniqueID,))
    pos = cursor.fetchone()
    position = pos[0]

    cursor.execute("DELETE FROM waitlist WHERE uniqueID = ?", (uniqueID,))

    cursor.execute("SELECT latestTs, phoneNum FROM people WHERE uniqueID = ?", (uniqueID,))
    added = cursor.fetchone()
    stateTime = datetime.now().strftime(datetimeFormat)
    
    #'0' is arrived; '1' is no-show; '2' is cancelled
    if state == "0":
        cursor.execute("UPDATE timestamps SET arrived = ? WHERE uniqueID = ? AND added = ?", (stateTime, uniqueID, added[0],))
    elif state == "1":
        cursor.execute("UPDATE timestamps SET noShow = ? WHERE uniqueID = ? AND added = ?", (stateTime, uniqueID, added[0],))
        if added[1] != "0":
            phoneNum = "+1" + added[1]
            body = "Hey " + uniqueID + "\n\nA stand was available for you, but you did not arrive in around 5 minutes and so have been deemed a no show.\n\nNext time, if you think you cannot make it, please arrive at the shop before it is your turn and cancel your turn.\n\nThanks!"
            sendMessage(phoneNum,body)
    else:
        cursor.execute("UPDATE timestamps SET cancelled = ? WHERE uniqueID = ? AND added = ?", (stateTime, uniqueID, added[0],))

    cursor.execute("UPDATE waitlist SET position = position - 1 WHERE position > ?", (position,))

    conn.commit()
    ack["result"] = 1
    conn.close()
    return dumps(ack)

@application.post('/queryList')
def queryList():
    uniqueID = request.forms.get("uniqueID")
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    ack = {}
    numAhead = 0

    cursor.execute("SELECT position FROM waitlist WHERE uniqueID = ?", (uniqueID,))
    position = cursor.fetchone()

    cursor.execute("SELECT latestTs FROM people WHERE uniqueID = ?", (uniqueID,))
    time = cursor.fetchone()
    if time == None:
        ack["result"] = -1
        return dumps(ack)

    cursor.execute("SELECT stationAvailable FROM timestamps WHERE uniqueID = ? AND added = ?", (uniqueID, time[0]))
    stnAvl = cursor.fetchone()
    ack["stationAvailable"] = stnAvl[0]

    cursor.execute("SELECT phoneNum FROM people WHERE uniqueID = ?", (uniqueID,))
    phoneNum = cursor.fetchone()
    ack["phone"] = phoneNum[0]

    if position == None:
        ack["result"] = -1
        return dumps(ack)
    else:
        ack["result"] = position[0]

    conn.close()
    return dumps(ack)

@application.post('/refresh')
def refresh():
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    data = []

    cursor.execute("SELECT people.uniqueID, phoneNum, latestTs, firstName FROM people, waitlist WHERE people.uniqueID = waitlist.uniqueID ORDER BY position ASC")

    for row in cursor:
        data.append([row[0], row[1], row[2][-8:], row[3]])

    conn.close()
    return dumps(data)

@application.post('/sendTextMessage')
def sendTextMessage():
    position = request.forms.get("position")
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    ack = {}
    
    cursor.execute("SELECT people.uniqueID, latestTs, phoneNum FROM people, waitlist WHERE people.uniqueID = waitlist.uniqueID AND position = ?", (position,))
    top = cursor.fetchone()
    curTime = datetime.now().strftime(datetimeFormat)
    cursor.execute("UPDATE timestamps SET stationAvailable = ? WHERE uniqueID = ? AND added = ?", (curTime, top[0], top[1],))

    conn.commit()

    if top[2] == "0":
        ack["result"] = -2
        return dumps(ack)

    phoneNum = "+1" + top[2]
    body = "It is now your turn "+top[0]+"!!\n\nArrive at the workshop as soon as possible, or your turn will be cancelled."

    sendMessage(phoneNum,body)
    
    ack["result"] = 1

    conn.close()
    return dumps(ack)

def sendMessage(phoneNum,bodyOfMessage):
    message = client.messages.create(
       body=bodyOfMessage,
       to=phoneNum,
       from_=serverPhoneNum,
    )

@application.post('/verifyPin')
def verifyPin():
    ack = {}
    pin = request.forms.get("pin")

    if pin == "1234":
       ack["result"] = 1
    else:
	ack["result"] = 0

    return dumps(ack)

@application.post('/swap')
def swap():
    idOne = request.forms.get("idOne")
    idTwo = request.forms.get("idTwo")
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    ack = {}

    cursor.execute("SELECT position FROM waitlist WHERE uniqueID = ?", (idOne,))
    posOne = (cursor.fetchone())[0]

    cursor.execute("SELECT position FROM waitlist WHERE uniqueID = ?", (idTwo,))
    posTwo = (cursor.fetchone())[0]

    cursor.execute("UPDATE waitlist SET position = ? WHERE uniqueID = ?", (posOne, idTwo,))
    cursor.execute("UPDATE waitlist SET position = ? WHERE uniqueID = ?", (posTwo, idOne,))

    conn.commit()
    ack["result"] = 1
    conn.close()
    return dumps(ack)

@application.post('/countTotal')
def countTotal():
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    data = {}

    cursor.execute("SELECT count(*) FROM waitlist")
    count = cursor.fetchone()
    data["count"] = count[0]

    curDate = datetime.now().strftime(dateFormat)

    cursor.execute("SELECT added, arrived, endTime, noShow, cancelled, flushedFromWaitlist FROM timestamps WHERE dateAdded = ?", (curDate,))
    sumTime = 0
    totalPeople = 0

    for row in cursor:
        startTime = datetime.strptime(row[0], datetimeFormat)

        if row[2] != 'N/A':
            endTime = datetime.strptime(row[2], datetimeFormat)
            totalPeople += 1
        elif row[1] != 'N/A':
            endTime = datetime.strptime(row[1], datetimeFormat)
            totalPeople += 1
        elif row[3] != 'N/A':
            endTime = datetime.strptime(row[3], datetimeFormat)
            totalPeople += 1
        elif row[4] != 'N/A':
            endTime = datetime.strptime(row[4], datetimeFormat)
            totalPeople += 1
        elif row[5] != 'N/A':
            endTime = datetime.strptime(row[5], datetimeFormat)
            totalPeople += 1
        else:
            continue

        diff = endTime - startTime
        sumTime += diff.total_seconds()

    avgHours = 0
    avgMinutes = 0

    if totalPeople > 0:
        avgSeconds = sumTime // totalPeople
        avgMinutesTemp = avgSeconds // 60
        avgHours = avgMinutesTemp // 60
        avgMinutes = avgMinutesTemp - avgHours * 60

    data["avgHours"] = avgHours
    data["avgMinutes"] = avgMinutes

    conn.close()
    return dumps(data)

@application.post('/getStats')
def getStats():
    dateFrom = request.forms.get("dateFrom")
    dateTo = request.forms.get("dateTo")
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    data = {}

    cursor.execute("SELECT count(added) FROM timestamps WHERE dateAdded BETWEEN ? AND ?", (dateFrom, dateTo,))
    added = cursor.fetchone()

    msgWasSent = True
    cursor.execute("SELECT count(msgSent) FROM timestamps WHERE msgSent = ? AND dateAdded BETWEEN ? AND ?", (msgWasSent, dateFrom, dateTo,))
    msgSent = cursor.fetchone()

    cursor.execute("SELECT count(arrived) FROM timestamps WHERE arrived <> 'N/A' AND dateAdded BETWEEN ? AND ?", (dateFrom, dateTo,))
    arrived = cursor.fetchone()

    cursor.execute("SELECT count(endTime) FROM timestamps WHERE endTime <> 'N/A' AND dateAdded BETWEEN ? AND ?", (dateFrom, dateTo,))
    logbook = cursor.fetchone()

    cursor.execute("SELECT count(noShow) FROM timestamps WHERE noShow <> 'N/A' AND dateAdded BETWEEN ? AND ?", (dateFrom, dateTo,))
    noShow = cursor.fetchone()

    cursor.execute("SELECT count(cancelled) FROM timestamps WHERE cancelled <> 'N/A' AND dateAdded BETWEEN ? AND ?", (dateFrom, dateTo,))
    cancelled = cursor.fetchone()

    cursor.execute("SELECT count(flushedFromWaitlist) FROM timestamps WHERE flushedFromWaitlist <> 'N/A' AND dateAdded BETWEEN ? AND ?", (dateFrom, dateTo,))
    flushedFromWaitlist = cursor.fetchone()

    cursor.execute("SELECT added, arrived, endTime, noShow, cancelled, flushedFromWaitlist FROM timestamps WHERE dateAdded = ?", (curDate,))
    sumTime = 0
    totalPeople = 0

    for row in cursor:
        startTime = datetime.strptime(row[0], datetimeFormat)

        if row[2] != 'N/A':
            endTime = datetime.strptime(row[2], datetimeFormat)
            totalPeople += 1
        elif row[1] != 'N/A':
            endTime = datetime.strptime(row[1], datetimeFormat)
            totalPeople += 1
        elif row[3] != 'N/A':
            endTime = datetime.strptime(row[3], datetimeFormat)
            totalPeople += 1
        elif row[4] != 'N/A':
            endTime = datetime.strptime(row[4], datetimeFormat)
            totalPeople += 1
        elif row[5] != 'N/A':
            endTime = datetime.strptime(row[5], datetimeFormat)
            totalPeople += 1
        else:
            continue

        diff = endTime - startTime
        sumTime += diff.total_seconds()

    avgHours = 0
    avgMinutes = 0

    if totalPeople > 0:
        avgSeconds = sumTime // totalPeople
        avgMinutesTemp = avgSeconds // 60
        avgHours = avgMinutesTemp // 60
        avgMinutes = avgMinutesTemp - avgHours * 60

    data["added"] = added[0]
    data["msgSent"] = msgSent[0]
    data["arrived"] = arrived[0]
    data["logbook"] = logbook[0]
    data["noShow"] = noShow[0]
    data["cancelled"] = cancelled[0]
    data["flushedFromWaitlist"] = flushedFromWaitlist[0]
    data["avgHours"] = avgHours
    data["avgMinutes"] = avgMinutes

    conn.close()
    return dumps(data)

@application.post('/emptyWaitlist')
def emptyWaitlist():
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    ack = {}

    curTime = datetime.now().strftime(datetimeFormat)

    cursor.execute("SELECT waitlist.uniqueID, latestTs, phoneNum FROM waitlist, people WHERE waitlist.uniqueID = people.uniqueID")
    waitlistRows = cursor.fetchall()

    for row in waitlistRows:
        cursor.execute("UPDATE timestamps SET flushedFromWaitlist = ? WHERE uniqueID = ? AND added = ?", (curTime, row[0], row[1],))
        if row[2] != "0":
            body = "Bikechain is now closing.\n\nWe apologise for not fitting you in today. Come back next time!"
            phoneNum = "+1"+row[2]
            sendMessage(phoneNum, body)

    cursor.execute("DELETE FROM waitlist")

    conn.commit()
    conn.close()
    ack["result"] = 1
    return dumps(ack)

@application.post('/getLogs')
def getLogs():
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    data = []

    cursor.execute("SELECT uniqueID, added, msgSent, stationAvailable, arrived, endTime, noShow, cancelled, flushedFromWaitlist FROM timestamps")

    for row in cursor:
    	isItThere = "yes" if row[2] == 1 else "no"
    	data.append([row[0], row[1], isItThere, row[3], row[4], row[5], row[6], row[7], row[8]])

    conn.close()
    return dumps(data)

@application.post('/getNoShow')
def getNoShow():
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    data = []

    curDate = datetime.now().strftime(dateFormat)
    
    cursor.execute("SELECT uniqueID, added, msgSent, stationAvailable, noShow FROM timestamps WHERE noShow <> 'N/A' AND dateAdded = ?", ( curDate,))

    for row in cursor:
    	isItThere = "yes" if row[2] == 1 else "no"
	data.append([row[0], row[1][-8:], isItThere, row[3][-8:], row[4][-8:]])

    conn.close()
    return dumps(data)
	
@application.post('/reply')
def reply():
    fromNumber = request.forms.get("From")
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    ack = {}

    cursor.execute("SELECT uniqueID FROM people WHERE phoneNum = ?", (fromNumber,))
    uniqueID = cursor.fetchone()

    if uniqueID != None:
        message = request.forms.get("Body")
        message = message.replace(" ", "").lower()
        if message == "update":
            cursor.execute("SELECT position FROM waitlist WHERE uniqueID = ?", (uniqueID[0],))
            position = cursor.fetchone()
            if position != None:
                if position[0] == "1":
                    message = "Hey " + uniqueID[0] + " your turn is coming!!\n\nYou will receive a text message soon once a stand is available."
                    resp = twilio.twiml.Response()
                    resp.message(message)
                else:
                    actualPosition = position[0] - 1
                    message = "Hey " + uniqueID[0] + "!\n\nThe number of people ahead of you are: " + actualPosition
                    resp = twilio.twiml.Response()
                    resp.message(message)
            else:
                message = "If you want to check your position on the waitlist, send the keyword 'update' (without quotation marks)"
                resp = twilio.twiml.Response()
                resp.message(message)
        else:
            message = "If you want to check your position on the waitlist, send the keyword 'update' (without quotation marks)"
            resp = twilio.twiml.Response()
            resp.message(message)	
    else:
        message = "You need to provide your phone number in order to use this service"
        resp = twilio.twiml.Response()
        resp.message(message)

    conn.close()
    return dumps(ack)

@application.post('/logQuestions')
def logQuestions():
    userType = request.forms.get("userType")
    uniqueID = request.forms.get("uniqueID")
    firstName = request.forms.get("firstName")
    QOneNew = request.forms.get("QOneNew")
    QTwoNew = request.forms.get("QTwoNew")
    QThreeNew = request.forms.get("QThreeNew")
    QFourNew = request.forms.get("QFourNew")
    QOneAll = request.forms.get("QOneAll")
    QTwoAll = request.forms.get("QTwoAll")
    QThreeAll = request.forms.get("QThreeAll")
    QFourAll = request.forms.get("QFourAll")
    QFiveAll = request.forms.get("QFiveAll")
    QSixAll = request.forms.get("QSixAll")
    conn = sqlite3.connect('bcapp.sqlite')
    cursor = conn.cursor()
    ack = {}
    curTime = ""
    curDate = ""

    # '1' is a new user; '2' is a returning user
    if userType == "1":
        try:
            curTime = datetime.now().strftime(datetimeFormat)
            curDate = datetime.now().strftime(dateFormat)
            cursor.execute("INSERT INTO people(uniqueID, firstName, latestTs) VALUES(?,?,?)", (uniqueID, firstName, curTime,))
        except sqlite3.IntegrityError:
            conn.rollback()
            ack["result"] = 0
            conn.close()
            return dumps(ack)

        cursor.execute("INSERT INTO logbookNew VALUES(?,?,?,?,?,?)", (uniqueID, curDate, QOneNew, QTwoNew, QThreeNew, QFourNew,))
    else:
        cursor.execute("SELECT * FROM people WHERE uniqueID = ?", (uniqueID,))
        isUser = cursor.fetchone()
        if isUser == None:
            ack["result"] = 0
            conn.close()
            return dumps(ack)

    cursor.execute("INSERT INTO logbook VALUES(?,?,?,?,?,?,?,?)", (uniqueID, curDate, QOneAll, QTwoAll, QThreeAll, QFourAll, QFiveAll, QSixAll,))

    cursor.execute("SELECT latestTs FROM people WHERE uniqueID = ?", (uniqueID,))
	regTime = cursor.fetchone()
    cursor.execute("SELECT * FROM timestamps WHERE uniqueID = ? AND added = ? AND dateAdded = ?", (uniqueID, regTime[0], curDate,))
    isReg = cursor.fetchone()
    if isReg != None:
        cursor.execute("UPDATE timestamps SET endTime = ? WHERE uniqueID = ? AND added = ? AND dateAdded = ?", (curTime, uniqueID, regTime[0], curDate,))
    else:
        cursor.execute("INSERT INTO timestamps(uniqueID, added, dateAdded) VALUES(?,?,?)", (uniqueID, curTime, curDate,))

    ack["result"] = 1
    conn.commit()
    conn.close()
    return dumps(ack)


run(host = 'localhost', port = 8080)
