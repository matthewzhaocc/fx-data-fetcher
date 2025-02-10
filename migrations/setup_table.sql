CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE quote_data (
    time TIMESTAMPTZ NOT NULL,
    base_fx TEXT NOT NULL,
    quoted_fx TEXT NOT NULL,
    ask DOUBLE PRECISION NOT NULL,
    bid DOUBLE PRECISION NOT NULL
);

SELECT create_hypertable('quote_data', by_range('time'));

ALTER TABLE quote_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'base_fx'
);
