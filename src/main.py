'''
Created on Apr 17, 2015

@author: amitshah
'''
import paho.mqtt.client as mqtt
import tornado.ioloop
import tornado.websocket
import functools
import os
import tornado.web
import tornado.httpserver
import json
from cgi import maxlen
import collections
import MySQLdb as db

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
#client.loop_forever()

class OilDrumMonitorHandler(tornado.web.RequestHandler):
    def initialize(self,drums):
        self.drums = drums
        
    def get(self):
        value = dict()
        for d in drums:
            value[d]= list(drums[d])
        self.render("home.html",drums=self.drums,json_drums=json.dumps(value))
    
    
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    
    def initialize(self,drums):
        self.drums = drums
    
    clients = dict()
    def open(self):
        WebSocketHandler.clients[id(self)] = self
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(message)

    def on_close(self):
        WebSocketHandler.clients.pop(id(self))
        print("WebSocket closed")
        
import MySQLdb,sys

def insert(mac,level,timestamp):
    try:
        con = MySQLdb.connect(host='localhost', user='root', passwd='', db='levelMonitor')
        cur = con.cursor()
        cur.execute("INSERT INTO level(mac,timestamp,level) VALUES(%s,%s,%s)", (mac,int(timestamp),int(level)))
    except:
        print sys.exc_info()
        con.rollback()
    finally:
        if con:
            con.commit()
            con.close()
            
if __name__ == '__main__':
    
    
    
    drums = dict()
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        client.subscribe("sensor/level/#")
       

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        try:
            mac,level,timestamp = msg.payload.split("/")
            insert(mac,level,timestamp)
            data_point = {'mac':mac, 'time':timestamp, 'level':level}
            if not(drums.has_key(mac)):
                drums[mac] = collections.deque([],100)
            drums[mac].append(data_point)
            
            map(lambda x: x.on_message(json.dumps(data_point)),WebSocketHandler.clients.values())
        except:
            print('error unpacking')
        print('distributing data:' + msg.topic+" "+str(msg.payload))
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect("52.6.61.218", 1883, 60)
    client.loop_start()
    services = dict(drums=drums)
    settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), "template"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret= 'testing123',
        login_url='/login',
        xsrf_cookies=True,
    )  
    application = tornado.web.Application([
      (r"/", OilDrumMonitorHandler,services),
      (r"/stream", WebSocketHandler,services)]
      , **settings)
    
    sockets = tornado.netutil.bind_sockets(8888)
    #tornado.process.fork_processes(0)
    server = tornado.httpserver.HTTPServer(application)
    server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()
    
    
    
    
    sock = client.socket()
    io_loop = tornado.ioloop.IOLoop.current()
    def callback(fd,events):
        print 'we got data'
    io_loop.add_handler(sock.fileno(), callback, io_loop.READ)
    io_loop.start()
    
    
    pass