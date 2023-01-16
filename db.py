import pandas as pd
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime
import re

username='root'     
password='dtac1800' 
host="localhost"
port_db="3306"

Base=declarative_base()
engine=create_engine(f'mysql+mysqldb://{username}:{password}@{host}:{port_db}/cactidb')


class Ex_osnr_id(Base):
    __tablename__='ex_osnr_id'
    id=Column(Integer,primary_key=True)
    domain=Column(VARCHAR(20))
    endToEndOtnTrailId=Column(Integer)
    endToEndOtnTrailLabel=Column(VARCHAR(200))
    card_type=Column(VARCHAR(20))
    rate=Column(VARCHAR(20))
    src_ne=Column(VARCHAR(30))
    dst_ne=Column(VARCHAR(30))
    nom_route=Column(VARCHAR(200))

class Ex_osnr_record(Base):
    __tablename__='ex_osnr_record'
    index=Column(Integer,primary_key=True)
    id=Column(Integer)
    domain=Column(VARCHAR(20))
    date=Column(DateTime, default=datetime.datetime.utcnow)
    az_osnr_value=Column(VARCHAR(30))
    za_osnr_value=Column(VARCHAR(30))
    curr_route=Column(VARCHAR(200))

class Ex_osnr_card_received(Base):
    __tablename__='ex_osnr_card_received'
    index=Column(Integer,primary_key=True)
    card_type=Column(VARCHAR(20))
    rate=Column(VARCHAR(20))
    received_osnr=Column(Integer)


Base=declarative_base()

table_objects = [Ex_osnr_id.__table__,Ex_osnr_record.__table__,Ex_osnr_card_received.__table__]
Base.metadata.create_all(engine,tables=table_objects)

if __name__ == "__main__":
    Ex_osnr_id.__table__.drop(engine)
    Ex_osnr_record.__table__.drop(engine)
    Ex_osnr_card_received.__table__.drop(engine)