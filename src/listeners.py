import os
from box import Box
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from threading import Thread
import logging
import time

logger = logging.getLogger("alms")


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


def getConfig():
    return Box({
        "dbname":"postgres",
        "user": "postgres",
        "dbpass": os.environ.get("POSTGRES_PASSWORD"),
        "host": "postgres"
    })


def getDBConn():
    config = getConfig()
    return psycopg2.connect(
        dbname=config.dbname,
        user=config.user,
        password=config.dbpass,
        host=config.host
    )


class DBListener(Thread):
    def __init__(self, channel, conf, q):
        Thread.__init__(self)
        self.channel = channel
        self.conf = conf
        self.q = q
        self.registerTriggers()

    def triggerInsertSQL(self):
        on_type = " or ".join(self.conf)
        return "create trigger {0}_after after {1} on {0} for each row execute procedure table_change('{0}', '{0}');".format(self.channel, on_type)

    def registerTriggers(self):
        logger.info("Registering table triggers for %s", self.channel)
        with getDBConn() as conn:
            cur = conn.cursor()
            cur.execute("drop trigger if exists {0}_after on {0};".format(self.channel))
            cur.execute(self.triggerInsertSQL())

    def run(self):
        cnn = getDBConn()
        cnn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = cnn.cursor()
        cur.execute("LISTEN {};".format(self.channel))
        while True:
            time.sleep(5)
            cnn.poll()
            while cnn.notifies:
                n = cnn.notifies.pop()
                logger.info(" %s <- size(%s)", str(n.channel), len(n.payload))
                self.q.put(n)
