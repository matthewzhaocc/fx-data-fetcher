import os
import json
import asyncio
import datetime

import asyncpg
from websockets.asyncio.client import connect, ClientConnection

# Synchronously await a ack from the websocket for authentication success
async def sync_auth_validation(ws_conn: ClientConnection):
  while True:
    msg = await ws_conn.recv()
    if 'auth_success' in str(msg):
      return

async def create_pg_conn() -> asyncpg.Pool:
  connection_pool = await asyncpg.create_pool(os.environ.get("DB_CONNECTION"))
  return connection_pool

async def authenticate_connection(ws_conn: ClientConnection) -> None:
  authentication_message = json.dumps({"action":"auth","params":os.environ.get("POLYGON_AUTH_TOKEN")})
  await ws_conn.send(authentication_message)

async def subscribe_datastream(ws_conn: ClientConnection) -> None:
  subscribe_message = json.dumps({"action":"subscribe", "params":"C.*"})
  await ws_conn.send(subscribe_message)

async def insert_fx_data(pg_conn: asyncpg.Pool, source: str, dest: str, timestamp: int, bid: float, ask: float) -> None:
  converted_datetime = datetime.datetime.fromtimestamp(timestamp//1000)
  await pg_conn.execute('INSERT INTO quote_data (time, base_fx, quoted_fx, ask, bid) VALUES($1, $2, $3, $4, $5)', converted_datetime, source, dest, ask, bid)

async def get_fx_data(ws_conn: ClientConnection, pg_conn: asyncpg.Pool) -> None:
  while True:
    msg = await ws_conn.recv()
    parsed_msg = json.loads(msg)
    for currency_data in parsed_msg:
      # Filter out non currency pair trade data
      if 'p' not in currency_data:
        continue
      # only filter for USD as the source currency
      if 'USD/' in currency_data["p"]:
        source, dest = currency_data["p"].split("/")
        asyncio.create_task(insert_fx_data(pg_conn, source, dest, currency_data["t"], currency_data["b"], currency_data["a"]))
          
async def main():
  polygon_connection = await connect("wss://socket.polygon.io/forex")
  pg_pool = await create_pg_conn()
  await authenticate_connection(polygon_connection)
  await sync_auth_validation(polygon_connection)
  await subscribe_datastream(polygon_connection)
  await get_fx_data(polygon_connection, pg_pool)

if __name__ == "__main__":
  asyncio.run(main())