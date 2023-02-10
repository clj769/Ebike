from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

#configs
app = Flask(__name__)
#create database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ebike.db'
app.config["SECRET_KEY"] = "secretkey"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)
app.config.from_object(__name__)

@app.before_first_request
def create_table():
    db.create_all()
with app.app_context():
    db.create_all()
from ebike import routes