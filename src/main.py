from queue import Queue
import logging
import sys
from .listeners import DBListener, setupTableTriggerFunction
from .publisher import EventPublisher
import yaml

logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger("alms")
logger.setLevel(logging.INFO)


def main():
    try:
        with open('./config.yml', 'r') as conf:
            config = yaml.load(conf.read())
    except e:
        print('Do you have a config.yml?')

    # trigger setup
    setupTableTriggerFunction()

    # event queue
    dbevents = Queue()

    # rabbit publisher
    rabbit = EventPublisher(dbevents, 'amqp://guest:guest@rabbit/?connection_attempts=3&heartbeat_interval=3600')
    logger.info("starting publishing")
    rabbit.start()

    # Start listeners
    for channel in config['tables']:
        listener = DBListener(channel, config['tables'][channel], dbevents)
        listener.start()
