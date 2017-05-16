# alms
Simple listener for changes on Events, Membership, and Quotes tables in node-api and more!

### Basic overview
Table changes are now subscribable in rabbitmq. The alms service will add db triggers to tables based on a config found below (and in the repo). You can then create a queue (programaticly) and bind it to the alms exchange, then set your routing key to the table name and you're done!

### The config
```yaml
tables:
  # on the officers table we want both insert and update events
  officers:
    - insert
    - update
  events:
    - insert
  memberships:
    - insert
  # quotes and above only want inserts
  quotes:
    - insert
```
This config will have to be updated if you want more events.

### RabbitMQ configuration
Alms will publish to the alms exchange, it's a direct exchange meaning that the routing key has to match exactly. The routing key is just the table name. If you want events to be durable they need to go into a queue somewhere, by binding the queue to the exchange you can keep recieving messages even if your app isn't running, then dequeue them on next start up.
