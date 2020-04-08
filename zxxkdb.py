# coding=utf-8

import os
import json

from peewee import *
from datetime import date
from playhouse.sqlite_ext import JSONField

db = SqliteDatabase(os.getcwd() + '/zxxk.db')

class BaseModel(Model):
    class Meta:
        database = db

class Info(BaseModel):
    channelid = SmallIntegerField(null=True) #int
    displayprice = CharField(null=True) #str
    filetype = CharField(null=True)
    intro = TextField(null=True)
    softid = SmallIntegerField(primary_key=True)
    softname = TextField()
    softsize = SmallIntegerField(null=True)
    updatetime = CharField(null=True)
    createtime = DateField(default=date.today())
    groupid = SmallIntegerField(null=True)
    downloadurls = JSONField(default={})


def create_db(softid, softname, **kw):
    if db.is_closed() == True:
        db.connect()
    db.create_tables([Info])
    Info.create(softid=softid, softname=softname, **kw)
    db.close()


def create_or_update(softid, softname, **kw):
    
    # 数据库是否打开
    if db.is_closed() == True:
        db.connect()

    if not Info.table_exists():
        db.create_tables([Info])
    
    try:
        select_info= Info.select().where(Info.softid == softid).get()
        Info.update(softname=softname, **kw).where(Info.softid == softid).execute()
        db.close()
    except:
        select_info = Info.create(softid=softid, softname=softname, **kw)
        db.close()
    return select_info
    

def select_db(softid):
    if db.is_closed() == True:
        db.connect()
    
    try:
        info = Info.select().where(Info.softid == softid).get()
        db.close()
        return info
    except:
        return 'Error'
