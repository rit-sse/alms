import psycopg2
import os
from queue import Queue
from box import Box
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from eventlet.hubs import trampoline
from threading import Thread
import logging
import sys
import pika

logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger("alms")
logger.setLevel(logging.INFO)


def getConfig():
    return Box({
        "dbpass": os.environ.get("POSTGRES_PASSWORD")
    })


def getDBConn():
    config = getConfig()
    return psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password=config.dbpass,
        host="postgres"
    )


def setupTableTriggerFunction():
    """
    Creates the function that postgres will call on table change triggers
    """
    logger.info("Setting up table_change trigger function")
    conn = getDBConn()
    with conn.cursor() as cursor:
        setup = open('./setup.sql', 'r').read()
        cursor.execute(setup)
    conn.commit()
    conn.close()


class EventPublisher(Thread):
    def __init__(self, q, queues):
        Thread.__init__(self)
        self.registerRabbitExchange(queues)
        self.q = q

    def registerRabbitExchange(self, queues):
        logger.info("Setting up rabbit exchange")
        # TODO: handle connection dropping
        self.connection = pika.BlockingConnection(pika.ConnectionParameters("rabbit"))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='alms', type='direct', durable=True)

    def publishEvent(self, chan, payload):
        logger.info(" %s <- size(%s)", str(chan), len(payload))
        if self.connection.is_closed:
            logger.info("Reconnecting to rabbit")
            self.connectin.connect()
        self.channel.basic_publish(exchange='alms', routing_key=chan, body=payload)

    def run(self):
        while True:
            if not self.q.empty():
                e = self.q.get()
                self.publishEvent(e.channel, e.payload)


class DBListener(Thread):
    def __init__(self, channel, q):
        Thread.__init__(self)
        self.channel = channel
        self.q = q
        self.registerTriggers()

    def registerTriggers(self):
        logger.info("Registering table triggers for %s", self.channel)
        with getDBConn() as conn:
            cur = conn.cursor()
            cur.execute("drop trigger if exists {0}_after on {0};".format(self.channel))
            cur.execute("create trigger {0}_after after insert on {0} for each row execute procedure table_change('{0}', '{0}');".format(self.channel))

    def run(self):
        cnn = getDBConn()
        cnn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = cnn.cursor()
        cur.execute("LISTEN {};".format(self.channel))
        while 1:
            trampoline(cnn, read=True)
            cnn.poll()
            while cnn.notifies:
                n = cnn.notifies.pop()
                self.q.put(n)


def main():
    # subscribers
    subs = ["officers", "events", "memberships", "quotes"]

    # trigger setup
    setupTableTriggerFunction()

    # event queue
    dbevents = Queue()

    # rabbit publisher
    rabbit = EventPublisher(dbevents, subs)
    rabbit.start()

    # Start listeners
    for chan in subs:
        listener = DBListener(chan, dbevents)
        listener.start()
