# coding=utf-8

import os
import json

from peewee import *
from datetime import date
from playhouse.sqlite_ext import JSONField

db = SqliteDatabase(os.getcwd() + '/zxxk.db')

class ListField(Field):
    field_type = 'list'
    def db_value(self, value):
        return ','.join(value)
    def python_value(self, value):
        return value.split(',')


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


class Album(BaseModel):
    albumid = SmallIntegerField(primary_key=True)
    softids = ListField()
    downloadurls = JSONField(default={})


def create_db(softid, softname, **kw):
    if db.is_closed() == True:
        db.connect()
    db.create_tables([Info])
    Info.create(softid=softid, softname=softname, **kw)
    db.close()


def create_or_update_info(softid, softname, **kw):
    
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


def create_or_update_album(albumid, softids, **kw):
    
    # 数据库是否打开
    if db.is_closed() == True:
        db.connect()

    if not Album.table_exists():
        db.create_tables([Album])
    
    try:
        select_info= Album.select().where(Album.albumid == albumid).get()
        Album.update(softids=softids, **kw).where(Album.albumid == albumid).execute()
        db.close()
    except:
        select_info = Album.create(albumid=albumid, softids=softids, **kw)
        db.close()
    return select_info


def select_db(softid):
    if db.is_closed() == True:
        db.connect()
    
    try:
        if len(softid) == 6:
            info = Album.select().where(Album.albumid == softid).get()
        elif len(softid) == 8:
            info = Info.select().where(Info.softid == softid).get()
        db.close()
        return info
    except:
        return 'Error'
