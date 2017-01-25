const PGPubsub = require('pg-pubsub'),
    pg = require('pg'),
    fs = require('fs')
;

// Build postgres connection string from environment
const USER = process.env.PG_ENV_POSTGRES_USER || 'postgres';
const PASSWORD = process.env.PG_ENV_POSTGRES_PASSWORD;
const DB = process.env.pg_ENV_POSTGRES_DB || USER;
const HOST = process.env.DB_HOST_OVERRIDE || 'pg';
const CONN = `postgres://${USER}:${PASSWORD}@${HOST}:5432/${DB}`;

const client = new pg.Client(CONN);

client.connect((err) => {
    if (!err) {
        const sql = fs.readFileSync('./setup.sql');
        client.query(sql.toString('utf8'), (err) => {
            if (!err) {
                client.end((err) => {
                    if (!err) {
                        subscribeEventChanges((payload) => {
                            console.log(payload);
                        });
                    } else error(err);
                });
            } else error(err);
        });
    } else error(err);
});

function error(err) {
    console.error(err);
    process.exit(1);
}

function subscribeEventChanges(cb) {
    const pubsubInstance = new PGPubsub(CONN);
    pubsubInstance.addChannel('ssevents', (payload) => {
        cb(payload);
    });
}
