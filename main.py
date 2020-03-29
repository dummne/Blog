# -*- coding: UTF-8 -*-

import random
import string
import json
import sqlite3
import time
import platform
from abc import ABC

from pathlib import Path
from base64 import b64encode
from uuid import uuid4

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.auth


class BaseHandler(tornado.web.RequestHandler, ABC):
    def __init__(self):
        self.resp = dict.fromkeys(["success", "msg", "data"])

    def initialize(self):
        # self.resp = dict.fromkeys(["success", "msg", "data"])
        pass

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        # self.set_header("Access-Control-Allow-Headers", "X-Requested-With, Origin, Referer, User-Agent")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE")
        self.set_header("Access-Control-Max-Age", "3600")
        self.set_header("Content-Type", "application/json")

    def get_current_user(self):
        mail = self.get_secure_cookie('mail')
        if mail:
            return mail
        return None

    def options(self):
        print("options")
        self.set_status(204)
        self.finish()


class UserHandler(BaseHandler, ABC):
    # 同步基本信息
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        self.resp['success'] = True
        self.resp['msg'] = ''
        self.resp['data'] = ''
        self.write(self.resp)

    # 用户登录
    def post(self, *args, **kwargs):
        try:
            body = json.loads(self.request.body)
        except ValueError:
            self.resp['success'] = False
            self.resp['msg'] = "message format error"
            self.write(self.resp)
            return None

        mail = body.get('mail', None)
        password = body.get('password', None)

        if mail and password:
            cur = self.application.db.execute("SELECT * FORM user WHERE mail='%s'" % mail)
            user = cur.fetchone()
            if user and user[2] == password:
                tags = user[4]
                self.resp['success'] = True
                self.resp['msg'] = 'login success'
                self.resp['data'] = {
                    'mail': user[1],
                    'phone': user[3],
                    'tags': tags.split('|'),
                    'name': user[5],
                    'prefix': user[6],
                    'signature': user[7],  # 个性签名
                    'identity': user[8],  # 身份，normal, trader, admin
                    'addr': user[9],  # 收获地址
                    'head': user[10],  # 头像
                }
                # 设置 cookie
                self.set_secure_cookie('mail', mail)
            else:
                self.resp['success'] = False
                self.resp['msg'] = 'login failed'

            self.write(self.resp)

    # 更新用户信息
    @tornado.web.authenticated
    def patch(self, *args, **kwargs):
        try:
            body = json.load(self.request.body)
        except ValueError:
            self.resp['success'] = False
            self.resp['msg'] = 'message format error'
            self.write(self.resp)
            return None

        mail = self.current_user
        password = body.get('password', None)
        if password:
            self.application.db.execute("UPDATE user SET password='%s' WHERE mail='%s'" % (password, mail))
        tags = body.get('tags', None)
        if tags:
            self.application.db.execute("UPDATE user SET tags='%s' WHERE mail='%s'" % (tags, mail))
        name = body.get('uname', None)
        if name:
            self.application.db.execute("UPDATE user SET uname='%s' WHERE mail='%s'" % (name, mail))
        prefix = body.get('prefix', None)
        if prefix:
            self.application.db.execute("UPDATE user SET prefix='%s' WHERE mail='%s'" % (prefix, mail))
        addr = body.get('addr', None)
        if addr:
            self.application.db.execute("UPDATE user SET addr='%s' WHERE mail='%s'" % (addr, mail))
        head = body.get('head', None)
        if head:
            self.application.db.execute("UPDATE user SET head='%s' WHERE mail='%s'" % (head, mail))
        self.application.db.commit()

    # 用户退出
    @tornado.web.authenticated
    def delete(self, *args, **kwargs):
        # self.clear_cookie()
        pass


class LogonHandler(BaseHandler, ABC):
    # 用户注册
    def post(self, *args, **kwargs):
        try:
            body = json.load(self.request.body)
        except ValueError:
            self.resp['success'] = False
            self.resp['msg'] = 'message format error'
            self.resp['data'] = ''
            self.write(self.resp)
            return None

        mail = body.get('mail', None)
        if mail:
            # 查询数据库，此用户是否存在
            cursor = self.application.db.execute("SELECT mail FROM user WHERE mail = '%s'" % mail)
            if not cursor.fetchone():
                self.resp['success'] = False
                self.resp['msg'] = 'user is already exists'
                self.resp['data'] = ''
            else:
                password = body.get('password', None)
                tags = '|'.join(body.get('tags', None))
                phone = body.get('phone', None)
                name = body.get('name', None)
                prefix = body.get('prefix', None)
                head = 'img/default.jpeg'
                cur = self.application.db.execute("INSERT INTO user (mail, password, tags, phone, uname, prefix, head) \
                                            VALUES(?,?,?,?,?,?,?)", (mail, password, tags, phone, name, prefix, head))
                self.application.db.commit()
                cur.close()
                self.resp['success'] = True
                self.resp['msg'] = 'logon success'
                self.resp['data'] = ''
        else:
            self.resp['success'] = False
            self.resp['msg'] = 'message error'
            self.resp['data'] = ''

        self.write(self.resp)


class UploadHandler(BaseHandler, ABC):
    def post(self, *args, **kwargs):
        files = self.request.files['avatar']
        for meta in files:
            file_name = meta['filename']

            image = Path(file_name)
            ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 16))

            with open(Path('img').joinpath(ran_str + image.suffix), 'wb') as up:
                up.write(meta['body'])

        self.resp['success'] = True
        self.resp['msg'] = ""
        self.resp['data'] = str(Path('img').joinpath(ran_str + image.suffix))

        self.write(self.resp)


class BBSHandler(BaseHandler, ABC):
    def get(self, *args, **kwargs):  # 获取所有帖子
        info = []
        article = {}
        rows = self.application.db.execute("SELECT * FROM bbs")
        for row in rows:
            article['id'] = row[0]
            article['title'] = row[1]
            article['author'] = row[2]
            article['ctime'] = row[3]
            article['summary'] = row[4]
            info.append(article)

        self.resp['success'] = True
        self.resp['msg'] = 'success'
        self.resp['data'] = info
        self.write(self.resp)

    def post(self, *args, **kwargs):  # 发表评论，发表帖子
        try:
            body = json.loads(self.request.body)
        except ValueError:
            self.resp['success'] = False
            self.resp['msg'] = 'message format error'
            self.write(self.resp)
            return None

        title = body.get('title', None)
        author = body.get('author', None)
        ctime = time.time()
        summary = body.get('summary', None)
        self.application.db.execute("INSERT INTO bbs(title, author, ctime, summary) "
                                    "VALUES(?,?,?,?,?)", (title, author, ctime, summary))
        self.application.db.commit()
        self.resp['success'] = True
        self.resp['msg'] = 'success'
        self.resp['data'] = ''
        self.write(self.resp)

    def delete(self):  # 删除评论，删除帖子
        id = 2  # ID 通过什么形式上传？？
        self.application.db.execute('DELETE FROM bbs WHERE id = %d' % id)
        self.application.db.commit()


class PostHandler(BaseHandler, ABC):
    def get(self):  # 获取某个帖子的评论
        info = []
        article = {}
        rows = self.application.db.execute("SELECT * FROM post")
        for row in rows:
            article['id'] = row[0]
            article['bbs_id'] = row[1]
            article['author'] = row[2]
            article['ctime'] = row[3]
            article['info'] = row[4]
            info.append(article)

        self.resp['success'] = True
        self.resp['msg'] = 'success'
        self.resp['data'] = info
        self.write(self.resp)

    def post(self):
        try:
            body = json.loads(self.request.body)
        except ValueError:
            self.resp['success'] = False
            self.resp['msg'] = 'message format error'
            self.resp['data'] = ''
            self.write(self.resp)
            return None

        bbs_id = body.get('bbs_id', None)
        author = body.get('author', None)
        ctime = time.time()
        summary = body.get('summary', None)
        self.application.db.execute("INSERT INTO article (bbs_id, author, ctime, info) VALUES(?,?,?,?)",
                                    (bbs_id, author, ctime, summary))
        self.application.db.commit()

    def delete(self):
        pass


class ReplyHandler(BaseHandler, ABC):
    def get(self):
        info = []
        article = {}
        rows = self.application.db.execute("SELECT * FROM reply")
        for row in rows:
            article['id'] = row[0]
            article['post_id'] = row[1]
            article['s_auth'] = row[2]
            article['d_auth'] = row[3]
            article['ctime'] = row[4]
            article['info'] = row[5]
            info.append(article)

        self.resp['success'] = True
        self.resp['msg'] = 'success'
        self.resp['data'] = info
        self.write(self.resp)

    def post(self):
        try:
            body = json.loads(self.request.body)
        except ValueError:
            self.resp['success'] = False
            self.resp['msg'] = 'message format error'
            self.resp['data'] = ''
            self.write(self.resp)
            return None

        post_id = body.get('post_id', None)
        s_auth = body.get('s_auth', None)
        d_auth = body.get('d_auth', None)
        info = body.get('info', None)
        ctime = time.time()

        self.application.db.execute('INSERT INTO reply(post_id, s_auth, d_auth, ctime, info) VALUES(?,?,?,?,?)',
                                    (post_id, s_auth, d_auth, ctime, info))
        self.application.db.commit()

        self.resp['success'] = True
        self.resp['msg'] = 'success'
        self.resp['data'] = ''
        self.write(self.resp)

    def delete(self):
        pass


class MallHandler(BaseHandler, ABC):
    def get(self, *args, **kwargs):
        pass  # 获取商品信息

    def post(self, *args, **kwargs):
        pass  # 下单购买商品


class TTHandler(BaseHandler, ABC):
    def get(self):
        pass

    def post(self):
        pass


class IMHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        pass
        # 新用户连接需要保存

    def on_message(self):  # 客户端发送消息 A --> B
        pass

    def on_close(self):  # 客户端断开连接
        pass

    def close(self):  # 服务端断开连接
        pass


class Application(tornado.web.Application):
    def __init__(self):
        # route table
        handlers = [
            (r"/login", UserHandler),
            (r"/logon", LogonHandler),
            (r"/upload", UploadHandler),
            (r"/img/(.*)", tornado.web.StaticFileHandler),
            (r"/", IndexHandler)
        ]

        settings = {
            "cookie_secret": bytes.decode(b64encode(uuid4().bytes + uuid4().bytes)),
            "static_path": Path().cwd().joinpath('img'),
            "login_url": "/login"
        }

        super(Application, self).__init__(handlers, **settings)
        self.db = sqlite3.connect("market.db")

    def __del__(self):
        self.db.close()


class IndexHandler(tornado.web.RequestHandler, ABC):
    # @tornado.web.authenticated
    def get(self):
        user = self.current_user
        print(type(user))
        # print(self.current_user)
        # print(user.encode())
        self.write("hello")

    def post(self):
        # try:
        #    body = json.loads(self.request.body)
        # except ValueError:
        #     self.finish("error")
        #     return None

        self.set_secure_cookie('session_id', "1234")

        self.finish()

    def get_current_user(self):
        return str(self.get_secure_cookie('session_id'))


if __name__ == "__main__":

    if platform.system() == "Windows":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 创建目录
    Path().cwd().joinpath('img').mkdir(parents=True, exist_ok=True)
    app = Application()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()
