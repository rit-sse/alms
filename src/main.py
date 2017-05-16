from queue import Queue
import logging
import sys
from .listeners import DBListener, getDBConn, setupTableTriggerFunction
from .publisher import EventPublisher

logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger("alms")
logger.setLevel(logging.INFO)


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
