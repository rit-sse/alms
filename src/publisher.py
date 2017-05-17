import logging
from threading import Thread
import pika

logger = logging.getLogger("alms")


class EventPublisher(Thread):
    def __init__(self, q, url):
        Thread.__init__(self)
        self._url = url
        self.q = q

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the onConnectionOpen method
        will be invoked by pika. If you want the reconnection to work, make
        sure you set stop_ioloop_onClose to False, which is not the default
        behavior of this adapter.

        :rtype: pika.SelectConnection

        """
        logger.info('Connecting to %s', self._url)
        return pika.SelectConnection(pika.URLParameters(self._url),
                                     self.onConnectionOpen,
                                     stop_ioloop_on_close=False)

    def onConnectionOpen(self, unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :type unused_connection: pika.SelectConnection

        """
        logger.info('Connection opened')
        self.addOnConnectionCloseCallback()
        logger.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.onChannelOpen)

    def onChannelOpen(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        logger.info('Channel opened')
        self._channel = channel
        self.registerRabbitExchange()

    def addOnConnectionCloseCallback(self):
        """This method adds an on close callback that will be invoked by pika
        when RabbitMQ closes the connection to the publisher unexpectedly.

        """
        logger.info('Adding connection close callback')
        self._connection.add_on_close_callback(self.onConnectionClosed)

    def onConnectionClosed(self, connection, reply_code, reply_text):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection connection: The closed connection obj
        :param int reply_code: The server provided reply_code if given
        :param str reply_text: The server provided reply_text if given

        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            logger.warning('Connection closed, reopening in 5 seconds: (%s) %s',
                           reply_code, reply_text)
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        """Will be invoked by the IOLoop timer if the connection is
        closed. See the onConnectionClosed method.

        """
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()

        # Create a new connection
        self._connection = self.connect()

        # There is now a new connection, needs a new ioloop to run
        self._connection.ioloop.start()

    def registerRabbitExchange(self):
        logger.info("Setting up rabbit exchange")
        self._channel.exchange_declare(exchange='alms', type='direct', durable=True)

    def publishEvent(self, chan, payload):
        logger.info(" %s -> published", chan)
        self._channel.basic_publish(exchange='alms', routing_key=chan, body=payload)

    def ackLocalQueue(self):
        if not self.q.empty():
            e = self.q.get()
            self.publishEvent(e.channel, e.payload)
        self._connection.add_timeout(0.2, self.ackLocalQueue)

    def run(self):
        self._connection = self.connect()
        self._connection.add_timeout(0.2, self.ackLocalQueue)
        self._connection.ioloop.start()
