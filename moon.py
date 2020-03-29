# -*- coding: UTF-8 -*-

import sqlite3
import time

if __name__ == '__main__':
    a = ['hello', 'hi', 'Tom', 'Mark', 'jary']
    s = '|'.join(a)
    print(s)

    conn = sqlite3.connect("test.db")
    test_sql = """
    CREATE TABLE IF NOT EXISTS ss(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rtime REAL NULL,
        t1 TEXT NULL
    );
    """

    conn.execute(test_sql)
    conn.commit()

    conn.execute('INSERT INTO ss(rtime, t1) VALUES(?, ?)', (time.time(), s))
    conn.commit()

    cur = conn.execute("SELECT * FROM ss")
    for row in cur:
        print(row[0])
        print(row[1])
        print(time.asctime(time.localtime(row[1])))
        print(row[2])
        print(type(row[2]))
        print(s.split('|'))

    conn.close()

    sql_str = """
    CREATE TABLE IF NOT EXISTS user(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mail VARCHAR(64) NULL,
        password VARCHAR(64) NULL,
        tags TEXT NULL,
        phone VARCHAR(12) NULL,
        uname VARCHAR(64) NULL,
        prefix VARCHAR(12) NULL,
        signature VARCHAR(128) NULL,
        uid VARCHAR(12) NULL,
        addr VARCHAR(128) NULL,
        head VARCHAR(64) NULL,
    );
    CREATE TABLE IF NOT EXISTS forum(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(128) NOT NULL,
        author VARCHAR(64) NOT NULL,
        ctime REAL NOT NULL,
        introduction TEXT NULL,
    );
    CREATE TABLE IF NOT EXISTS comment(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        forum INTEGER NOT NULL,         # 对应帖子
        author VARCHAR(64) NOT NULL,    # 评论者
        ctime REAL NOT NULL,         # 评论时间
        message TEXT NULL,          # 评论内容
        # reply INTEGER NULL,        # 回复
    );
    CREATE TABLE IF NOT EXISTS mall(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gname VARCHAR(128) NULL,    # 商品名称
        seller VARCHAR(64) NULL,    # 卖家
        sketch VARCHAR(128) NULL,   # 商品简述
    );
    CREATE TABLE IF NOT EXISTS order(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ctime REAL NOT NULL,
    );
    """

    # 快递鸟