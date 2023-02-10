import math
import os
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from flask import render_template, redirect, url_for, flash
from flask import request
from sqlalchemy import extract
from flask_mail import Mail, Message
from threading import Thread
#plt.switch_backend('agg')

from ebike import app, db
from ebike.models import USER, RENTAL_LOG, VEHICLE, DEFECT_REPORT_LOG

path = os.getcwd()

frontResult={'username':'','rentstatus':'','rentingID':'','balance':'','rentingtime':''}
vehicledict={}

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'my.qgong@gmail.com'
app.config['MAIL_PASSWORD'] = 'zlcddkpztachrcum'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


#homepage
@app.route('/',methods=['GET'])
def main():
    return render_template('index.html')


#login
@app.route('/login', methods=['GET','POST'])
def login():
    global frontResult
    username = request.form.get('username')
    password = request.form.get('password')
    user = USER.query.filter_by(Username=username,User_Password=password).first()
    print(username)
    print(password)
    if user:
        frontResult['username'] = username
        return redirect('/map')
    else:

        #return redirect('/',**frontResult)
        return redirect('/')

#map
@app.route('/map',methods=['GET','POST'])
def map():
    global frontResult

    # store into dataframe and export txt for map
    if frontResult['username']=='' and os.path.exists(path+'/ebike/static/exvehicles.txt'):
        os.remove(path+'/ebike/static/exvehicles.txt')

    vehiclesTxt = db.session.query(VEHICLE.Vehicle_ID, VEHICLE.Vehicle_Type, VEHICLE.Vehicle_Operational_Status,
                                   VEHICLE.Vehicle_Defect_Status,
                                   VEHICLE.Vehicle_Battery, VEHICLE.Vehicle_Latitude, VEHICLE.Vehicle_Longitude,
                                   VEHICLE.Vehicle_Operational_Status)
    vehiclesTxt = pd.DataFrame(vehiclesTxt)
    if frontResult['username'] != '':
        vehiclesTxt.to_csv(path + '/ebike/static/exvehicles.txt', index=False)


    #store into a dict for front end
    global vehicledict
    vehicles = VEHICLE.query.all()
    for vehicle in vehicles:
        vehicledict[vehicle.Vehicle_ID] = [vehicle.Vehicle_Type,vehicle.Vehicle_Operational_Status,
                                           vehicle.Vehicle_Defect_Status,vehicle.Vehicle_Battery, vehicle.Vehicle_Longitude,vehicle.Vehicle_Latitude]
    #print(vehicledict)

    if frontResult['username']!='':
        user = USER.query.filter_by(Username=frontResult['username']).first()
        rentinfo = RENTAL_LOG.query.filter_by(Rental_User_ID=user.User_ID,Rental_End_Time=None).first()

        if rentinfo:
            #user already rent a vehicle
            frontResult['rentstatus'] = '1'  #1 means rented a vehicle, null means not rent a vehicle
            frontResult['rentingID'] = rentinfo.Rental_Vehicle_ID #the rented vehicle ID, null means not rent a vehicle
            frontResult['rentingtime'] = str(rentinfo.Rental_Start_Time)
        else:
            #user not rent a vehicle
            frontResult['rentstatus'] = ''
            frontResult['rentingID'] = ''
            frontResult['rentingtime'] = ''

        frontResult['balance'] = user.User_Balance
        #print(frontResult)
    # if request.method == 'POST':
    #users = db.session.query(USER.User_ID)
    #users = pd.DataFrame(users)
    #users.to_csv(path + '/ebike/static/users.txt', index=False)
    return render_template('mapDemo1610.html',**frontResult)

#user report a vehicle as defective
@app.route('/report',methods=['GET','POST'])
def report():
    global frontResult
    if request.method == 'GET':
        return render_template('vehicleClicked.html',**frontResult)
    if request.method == 'POST':
        reports = DEFECT_REPORT_LOG.query.all()
        did = len(reports)+1
        user = USER.query.filter_by(Username=frontResult['username']).first()
        duid = user.User_ID
        dvid = request.form.get('defectvid')
        vehicle  = VEHICLE.query.filter_by(Vehicle_ID=dvid).first()
        dvtype = vehicle.Vehicle_Type
        status = "defect"

        #change vehicle's defect status
        db.session.query(VEHICLE).filter_by(Vehicle_ID=dvid).update({VEHICLE.Vehicle_Defect_Status: 'defect'})
        db.session.commit()

        #add defect log
        reporttime = datetime.now()
        comment = request.form.get('defectcomment')
        defectlog = DEFECT_REPORT_LOG(did,dvid,duid,dvtype,status,reporttime,comment)
        db.session.add(defectlog)
        db.session.commit()
        return redirect('/map')


#user rent vehicle
@app.route('/rent',methods=['GET','POST'])
def rent():
    global frontResult
    if request.method == 'GET':
        return render_template('vehicleClicked.html', **frontResult)
    if request.method == 'POST':
        rentlogs = RENTAL_LOG.query.all()
        rid = len(rentlogs) + 1
        user = USER.query.filter_by(Username=frontResult['username']).first()
        ruid = user.User_ID
        rvid = request.form.get('vid')

        #change the vehicle operation status to inuse
        db.session.query(VEHICLE).filter_by(Vehicle_ID=rvid).update({VEHICLE.Vehicle_Operational_Status:'inuse'})
        db.session.commit()

        #add rent log
        rentlog = RENTAL_LOG(rid,ruid,rvid)
        db.session.add(rentlog)
        db.session.commit()
    return redirect('/map')


#user return vehicle
@app.route('/returnvehicle',methods=['GET','POST'])
def returnvehicle():
    global frontResult
    print(frontResult)
    if request.method == 'GET':
        return render_template('returnvehicle.html', **frontResult)
    if request.method == 'POST':
        user = USER.query.filter_by(Username=frontResult['username']).first()
        ruid = user.User_ID
        rentlog = RENTAL_LOG.query.filter_by(Rental_Vehicle_ID=frontResult['rentingID'],Rental_User_ID=ruid, Rental_End_Time=None).first()
        st = rentlog.Rental_Start_Time
        et = datetime.now()
        seconds = (et - st).total_seconds()
        #print(seconds)

        m,s = divmod(seconds,60)
        h,m = divmod(m,60)
        druation = str(int(h)) +':'+ str(int(m))+':'+str(int(s))
        #print(druation)

        #scooter 0.25 pound/15min, bike 0.5 pounds/15min, both cost 1% battery/5min
        ceil = math.ceil(seconds/900)
        vehicle = VEHICLE.query.filter_by(Vehicle_ID=frontResult['rentingID']).first()
        if vehicle.Vehicle_Type == "scooter":
            cost = 0.25*ceil
        if vehicle.Vehicle_Type == "bike":
            cost = 0.5*ceil

        initBattery = vehicle.Vehicle_Battery
        battery = initBattery - math.ceil(seconds/300)
        #print(battery)

        #update rent log
        db.session.query(RENTAL_LOG).filter_by(Rental_Vehicle_ID=frontResult['rentingID'],Rental_User_ID=ruid, Rental_End_Time=None). \
            update({RENTAL_LOG.Rental_End_Time: et, RENTAL_LOG.Rental_Amt: cost, RENTAL_LOG.Rental_Duration: druation})
        db.session.commit()

        #update the vehicle operation status back to available, update the battery and the location
        long = request.form.get('returnLong')
        lat = request.form.get('returnLat')
        db.session.query(VEHICLE).filter_by(Vehicle_ID=frontResult['rentingID']). \
            update({VEHICLE.Vehicle_Operational_Status: 'available',VEHICLE.Vehicle_Battery: battery,
                    VEHICLE.Vehicle_Longitude: float(long), VEHICLE.Vehicle_Latitude: float(lat)})
        db.session.commit()

        #update the user's balance, need to check if user's balance is enough
        balance = user.User_Balance - cost
        frontResult['balance'] = balance
        db.session.query(USER).filter_by(Username=frontResult['username']). \
            update({USER.User_Balance: balance})
        db.session.commit()
        if balance < 0:
            #user's balance is not enough
            return redirect('/charge')

        #reset global
        frontResult['rentstatus'] = ''
        frontResult['rentingID'] = ''
        frontResult['rentingtime'] = ''
        frontResult['balance'] = user.User_Balance
    return redirect('/map')


#user charged
@app.route('/charge', methods=['GET','POST'])
def charge():
    global frontResult
    if request.method == 'GET':
        return render_template('charge.html', **frontResult)
    if request.method == 'POST':
        #user add money
        user = USER.query.filter_by(Username=frontResult['username']).first()
        money = request.form.get('money')
        balance = user.User_Balance + int(money)
        db.session.query(USER).filter_by(Username=frontResult['username']). \
            update({USER.User_Balance: balance})
        db.session.commit()
        frontResult['balance'] = user.User_Balance

    return redirect('/map')


#dashboard page and redirect to other page
@app.route('/dashboard' ,methods=['GET','POST'])
def dashboard():
    global frontResult
    global vehicledict
    if frontResult['username'] != '':
        user = USER.query.filter_by(Username=frontResult['username']).first()
        #operator's dashboard, can charge,repair and move vehicles
        if user.User_Category=='operator':
            return render_template('operator.html',bikesdict=vehicledict)

        #manager's dashboard, can see the log
        elif user.User_Category=='manager':
            return render_template('manager.html')

        #normal user, can not see the dashboard
        else:
            return redirect('/login')

#operator's dashboard function(charge,move,repair a vehicle)
@app.route('/operation' ,methods=['GET','POST'])
def operation():
    if request.method =='POST':
        vid = int(request.form.get('vid'))#the key in dict is integer
        vtype = request.form.get('vtype')
        opstatus = 'available' #locked
        defectstatus = request.form.get('defectstatus')
        battery = request.form.get('battery')
        lat = request.form.get('lat')
        longitude = request.form.get('long')

        # update database
        if request.form.get('chargeBattery'):
            battery = 100
            db.session.query(VEHICLE).filter_by(Vehicle_ID=vid).update({VEHICLE.Vehicle_Battery: battery})
            db.session.commit()

        elif request.form.get('repair'):
            defectstatus = 'non'
            db.session.query(VEHICLE).filter_by(Vehicle_ID=vid).update({VEHICLE.Vehicle_Defect_Status: defectstatus})
            db.session.query(DEFECT_REPORT_LOG).filter_by(Defect_Vehicle_ID=vid,Defect_Repair_Timestamp=None). \
                update({DEFECT_REPORT_LOG.Defect_Repair_Timestamp: datetime.now(),DEFECT_REPORT_LOG.Defect_Comments: 'repaired'})
            db.session.commit()

        elif request.form.get('submit'):
            db.session.query(VEHICLE).filter_by(Vehicle_ID=vid). \
                update({VEHICLE.Vehicle_Battery: battery, VEHICLE.Vehicle_Operational_Status: opstatus, VEHICLE.Vehicle_Defect_Status: defectstatus,
                        VEHICLE.Vehicle_Type:vtype, VEHICLE.Vehicle_Longitude: float(longitude), VEHICLE.Vehicle_Latitude: float(lat)})
            db.session.commit()

        #update global
        vehicledict.update({vid: [vtype, opstatus,defectstatus, battery, longitude, lat]})
        #print(vehicledict)

    return render_template('operator.html', bikesdict=vehicledict)


#operator's dashboard function(add a new vehicle)
@app.route('/addvehicle' ,methods=['GET','POST'])
def addvehicle():
    if request.method =='POST':
        vnum = VEHICLE.query.all()
        vid = len(vnum)+1
        vtype = request.form.get('addvtype')
        opstatus = 'available' #locked
        defectstatus = request.form.get('adddefstatus')
        battery = request.form.get('addbattery')
        lat = request.form.get('addlat')
        longitude = request.form.get('addlong')

        #insert new vehicle into database
        newvehicle = VEHICLE(vid, vtype, opstatus, defectstatus, battery, longitude, lat)
        db.session.add(newvehicle)
        db.session.commit()

        #add global
        vehicledict[vid]= [vtype,opstatus,defectstatus, battery, longitude, lat]
        #print(vehicledict)

    return render_template('operator.html', bikesdict=vehicledict)


#manager's dashboard
@app.route('/manage', methods=['GET','POST'])
def manage():
    if request.method =='POST':
        plt.clf()
        #loop through each month
        for month in range(1, 13):
            #get all the rent logs according to month
            #print('This is month '+str(month))
            rentLogs = db.session.query(RENTAL_LOG).filter(extract('month', RENTAL_LOG.Rental_Start_Time) == month,).all()

            bikenum = 0 #this month user rented how many bikes
            scooternum = 0 #this month user rented how many scooters
            rentingTime1 = 0 #this month user rented <= 5min
            rentingTime2 = 0 #this month user rented 5-10min
            rentingTime3 = 0 #this month user rented 10-30min
            rentingTime4 = 0 #this month user rented 30-60min
            rentingTime5 = 0 #this month user rented >60min

            #check each log from that month, vid is the primary key
            for log in rentLogs:
                vehicle = VEHICLE.query.filter_by(Vehicle_ID=log.Rental_Vehicle_ID).first()
                st = log.Rental_Start_Time
                et = log.Rental_End_Time
                if et==None:
                    continue
                seconds = int((et - st).total_seconds())

                #check vehicle type
                if vehicle.Vehicle_Type == "bike":
                    bikenum +=1
                elif vehicle.Vehicle_Type == "scooter":
                    scooternum +=1

                #renting time [0,5],(5,10],(10,30],(30,60],(60,MAX)
                if seconds <= 300:
                    rentingTime1 +=1
                elif 300 < seconds <= 600:
                    rentingTime2 += 1
                elif 600 < seconds <= 1800:
                    rentingTime3 += 1
                elif 1800 < seconds <= 3600:
                    rentingTime4 += 1
                elif seconds > 3600:
                    rentingTime5 += 1

            #print(bikenum,scooternum, rentingTime1,rentingTime2,rentingTime3,rentingTime4,rentingTime5)

            #draw the charts
            #Pie Chart for rented type
            pieLabels = ['bike','scooter']
            pieValues = [bikenum,scooternum]
            colors = ['orange','blue']
            plt.subplot(121)
            plt.title('Renting Type for Month '+str(month))
            plt.pie(pieValues,labels=pieLabels,colors=colors,shadow=True,autopct='%1.1f%%',startangle=180)

            #Bar Chart for renting time
            plt.subplot(122)
            plt.title('Renting Time for Month '+str(month))
            barIndex = ['0-5','5-10','10-30','30-60','60+']
            plt.xlabel('Renting minutes')
            plt.ylabel('Number of Users')
            barValues = [rentingTime1,rentingTime2,rentingTime3,rentingTime4,rentingTime5]
            plt.bar(barIndex,barValues)

            #adjust the blank
            plt.subplots_adjust(left=0.1,right=0.95,wspace=0.8, hspace=0.3)

            #save the images
            plt.savefig(path+'/ebike/static/Month/image'+str(month)+'.jpg')
            plt.show()



    return render_template('manager.html')






#register
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method =='GET':
        return render_template('Signup.html')
    #read data from signup page, post values to insert to database
    if request.method =='POST':
        category = request.form.get('category')
        username = request.form.get('username')
        pwd = request.form.get('password')
        repwd = request.form.get('repassword')
        address = request.form.get('address')
        email = request.form.get('email')
        if pwd == repwd:
            users = USER.query.all()
            #0 is default balance
            user = USER(category,len(users)+1,username,address,email,repwd,0)
            db.session.add(user)
            db.session.commit()
            flash('Sign up successful! You can login now','green')
            return redirect(url_for('login'))
        return render_template('Signup.html')

# contactus page
@app.route('/contactus', methods=['GET','POST'])
def contactus():
    if request.method == 'GET':
        return render_template('contactus.html')
    if request.method == 'POST':
        user = request.form.get('user')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        msg = Message(subject=subject,sender='my.qgong@gmail.com',recipients=['mygongqiao@outlook.com'],body=user+' Email: '+email+"  Message: "+message)
        try:
            mail.send(msg)
            return render_template('index.html')
        except Exception as e:
            print(e)
            return 'Sending Fail'
    return render_template('contactus.html')


