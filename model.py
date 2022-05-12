from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_url_path='/static')
app.debug = True
app.config['SECRET_KEY'] = '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = Column(INTEGER, primary_key=True)
    username = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean)
    is_judge = Column(Boolean, default=False)

    def get_full_name(self):
        return f"{self.name} {self.last_name}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Game(db.Model):
    __tablename__ = 'game'
    id = Column(INTEGER, primary_key=True)
    set_id = Column(Integer(), nullable=False)
    judge_id = Column(Integer(), nullable=False)
    result = Column(Integer())
    is_active = Column(Boolean, default=False)
    current_question_id = Column(Integer(), nullable=True)
    last_answer = Column(String(), nullable=True)
    datetime = Column(DateTime, nullable=True)
    set_name = Column(String(), nullable=False)


class Question(db.Model):
    __tablename__ = 'question'
    id = Column(INTEGER, primary_key=True)
    name = Column(TEXT, nullable=False)
    answer = Column(TEXT, nullable=False)
    set_id = Column(Integer(), ForeignKey('set.id'))


class Set(db.Model):
    __tablename__ = 'set'
    id = Column(INTEGER, primary_key=True)
    name = Column(TEXT, nullable=False)
    questions = relationship('Question', backref='set')
