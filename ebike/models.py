from ebike import db
from datetime import datetime

#tables in database
class USER(db.Model):
    __tablename__ = 'user'
    User_Category = db.Column(db.String(20), nullable=False)
    User_ID = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(20), unique=True, nullable=False)
    User_Address = db.Column(db.String(100), nullable=False)
    User_Email = db.Column(db.String(50), unique=True, nullable=False)
    User_Password = db.Column(db.String(100), nullable=False)
    User_Balance = db.Column(db.Float, nullable=False)
    #not the column but relationships
    #logs = db.relationship('RENTAL_LOG', backref='customer', lazy=True) #the order when user rent a vehicle
    #reports = db.relationship('DEFECT_REPORT_LOG', backref='customer', lazy=True) #the report when user report a defect

    def __init__(self,User_Category,User_ID,Username,User_Address,User_Email,User_Password,balance):
        self.User_Category = User_Category
        self.User_ID = User_ID
        self.Username = Username
        self.User_Address = User_Address
        self.User_Email = User_Email
        self.User_Password = User_Password
        self.User_Balance = balance


class VEHICLE(db.Model):
    __tablename__ = 'vehicle'
    Vehicle_ID = db.Column(db.Integer, primary_key=True)
    Vehicle_Type = db.Column(db.String(20), nullable=False) #bike or scooter
    Vehicle_Operational_Status = db.Column(db.String(20), nullable=False) #avliable or occupied
    Vehicle_Defect_Status = db.Column(db.String(20), nullable=False) #"Defective" or "Non-defective"
    Vehicle_Battery = db.Column(db.Integer) #show in front end
    Vehicle_Longitude = db.Column(db.Float, nullable=False)
    Vehicle_Latitude = db.Column(db.Float, nullable=False)

    def __init__(self,vid,vtype,vopstatus,vdefstatus,battery,longitude,latitude):
        self.Vehicle_ID = vid
        self.Vehicle_Type = vtype
        self.Vehicle_Operational_Status = vopstatus
        self.Vehicle_Defect_Status = vdefstatus
        self.Vehicle_Battery = battery
        self.Vehicle_Longitude = longitude
        self.Vehicle_Latitude = latitude

    def keys(self):
        return['Vehicle_ID','Vehicle_Type','Vehicle_Operational_Status','Vehicle_Defect_Status','Vehicle_Battery','Vehicle_Longitude','Vehicle_Latitude']
    def __getitem__(self, item):
        return self.__getattribute__(item)



class RENTAL_LOG(db.Model):
    __tablename__ = 'rental_log'
    Rental_Log_ID = db.Column(db.Integer, primary_key=True)
    Rental_User_ID = db.Column(db.Integer, db.ForeignKey("user.User_ID"), nullable=False)
    Rental_Vehicle_ID = db.Column(db.Integer, db.ForeignKey("vehicle.Vehicle_ID"), nullable=False)
    Rental_Start_Time = db.Column(db.DateTime, nullable=False, default=datetime.now())
    Rental_End_Time = db.Column(db.DateTime)
    Rental_Duration = db.Column(db.String(20))
    Rental_Amt = db.Column(db.Float)

    def __init__(self,rid,ruid,rvid):
        self.Rental_Log_ID = rid
        self.Rental_User_ID = ruid
        self.Rental_Vehicle_ID = rvid


class DEFECT_REPORT_LOG(db.Model):
    __tablename__ = 'defect_report_log'
    Defect_Log_ID = db.Column(db.Integer, primary_key=True)
    Defect_Vehicle_ID = db.Column(db.Integer, db.ForeignKey("vehicle.Vehicle_ID"), nullable=False)
    Defect_Reporting_User_ID = db.Column(db.Integer, db.ForeignKey("user.User_ID"), nullable=False)
    Defect_Vehicle_Type = db.Column(db.String(20), nullable=False)
    Vehicle_Defect_Status = db.Column(db.String(20), nullable=False)
    Defect_Reporting_Timestamp = db.Column(db.DateTime, nullable=False)
    Defect_Repair_Timestamp = db.Column(db.DateTime)
    Defect_Comments = db.Column(db.String(600))

    def __init__(self,did,dvid,duid,dvtype,status,reporttime,comments):
        self.Defect_Log_ID = did
        self.Defect_Reporting_User_ID = duid
        self.Defect_Vehicle_ID = dvid
        self.Defect_Vehicle_Type = dvtype
        self.Vehicle_Defect_Status = status
        self.Defect_Reporting_Timestamp = reporttime
        self.Defect_Comments = comments