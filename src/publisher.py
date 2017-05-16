import logging
from threading import Thread
import pika

logger = logging.getLogger("alms")


class EventPublisher(Thread):
    def __init__(self, q):
        Thread.__init__(self)
        self.registerRabbitExchange()
        self.q = q

    def registerRabbitExchange(self):
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
