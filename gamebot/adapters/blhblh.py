# blhblh.py
import asyncio
import socketio
import httpx
import socketio.exceptions
import pydantic
import enum
import datetime
import logging # Import logging
from typing import Optional, Any
from cachetools import LRUCache
import base64


# Configure logging for this module
logger = logging.getLogger(__name__)
# By default, handlers are not attached, main.py will configure the root logger

# --- Pydantic Models ---
class Gender(enum.StrEnum):
    M = 'M'
    F = 'F'

class Message(pydantic.BaseModel):
    user: str
    name: str
    text: str
    age: int
    gender: Gender
    likes: int
    profile: str
    time: datetime.datetime
    pic: pydantic.HttpUrl | None = None

    def __hash__(self):
        return hash((self.user, self.text, self.profile, self.time, self.pic))

class PostMessage(pydantic.BaseModel):
    text: str
    pic: bytes | None = None

class AckResult(pydantic.BaseModel):
    result: str
    pic_url: pydantic.HttpUrl | None = pydantic.Field(..., alias='picUrl')

    @pydantic.field_validator('pic_url', mode='before')
    @classmethod
    def empty_str_to_none(cls, value: str) -> str | None:
        if value == '':
            return None
        
        return value



class BlhBlhAdapter:
    """
    Adapter class to interact with the blhblh.be service.
    Handles login, Socket.IO connection, message polling,
    and publishing messages to a PubSub instance.
    """

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.cookie: Optional[str] = None
        self.sio = socketio.AsyncClient()
        self.dedup_cache = LRUCache(maxsize=2**10)
        self.only_after = datetime.datetime.now(datetime.timezone.utc)
        self.subscribers: dict[str, asyncio.Queue] = {}
        self.topic = asyncio.Queue()
        self.http_client = httpx.Client()
        self.sio_connected_event = asyncio.Event()
        self.sio_connected_event.clear()

        # Register Socket.IO event handlers
        @self.sio.event
        async def connect():
            logger.info("BlhBlhAdapter: Connected to Socket.IO server!")
            self.sio_connected_event.set()

        @self.sio.event
        async def disconnect(reason):
            logger.info(f"BlhBlhAdapter: Disconnected from Socket.IO server. ({reason})")
            self.sio_connected_event.clear()

        @self.sio.event
        async def messages(data: list[dict[str, Any]]):
            try:
                parsed = [Message.model_validate(msg) for msg in data]
                only_after = [msg for msg in parsed if msg.time > self.only_after]

                for msg in sorted(only_after, key=lambda x: x.time):
                    message_hash = hash(msg)
                    if message_hash not in self.dedup_cache:
                        self.dedup_cache[message_hash] = True
                        await self._publish(msg)

            except pydantic.ValidationError as e:
                logger.error(f"BlhBlhAdapter: Pydantic validation error for event '{messages.__name__}': {e}", exc_info=True)
            except Exception as e:
                logger.error(f"BlhBlhAdapter: An unexpected error processing message event: {e}", exc_info=True)


        @self.sio.on('onUserInfo')
        async def user_info_handler(data):
            logger.info('ignoring user info...')


        @self.sio.event
        async def message(event, sid, data):
            """
            Handles incoming generic Socket.IO messages.
            Parses them and publishes valid Message events.
            """
            print(event, sid, data)
 

    async def _login(self) -> str:
        """
        Performs HTTP login to extract the cookie.
        """
        async with httpx.AsyncClient() as http_client:
            res = await http_client.post(
                'https://blhblh.be/api/login',
                json={
                    'user': self.username,
                    'password': self.password
                },
            )
            res.raise_for_status() # Raise an exception for HTTP errors
            self.cookie = '; '.join([f'{cookie_name}={cookie_value}' for cookie_name, cookie_value in http_client.cookies.items()])
            logger.info("BlhBlhAdapter: Successfully logged in and extracted cookie.")
            return self.cookie
        

    async def reconnect_task(self):

        while True:
            if not self.sio.connected:
                self.cookie = await self._login()
                if not self.cookie:
                    logger.error('Can not obtain login cookie.')
                    return
                
                logger.info('Connecting to Socket.io')
                await self.sio.connect(
                    'https://blhblh.be/',
                    headers={'Cookie': self.cookie},
                    socketio_path='socket.io',
                    retry=True,
                )

            await asyncio.sleep(60)



    async def connect_and_poll(self):
        """
        Logs in, connects to Socket.IO, and continuously polls for messages.
        """
        logger.info("BlhBlhAdapter task started.")

        while True:
            try:
                await self.sio_connected_event.wait()
                while self.sio.connected:
                    try:
                        await self.sio_connected_event.wait()
                        await self.sio.emit('fetchMessages', '')
                    except socketio.exceptions.DisconnectedError:
                        logger.info("BlhBlhAdapter: Socket.IO client disconnected during polling.")
                        break
                    except asyncio.CancelledError:
                        logger.info("BlhBlhAdapter: connect_and_poll task cancelled.")
                        break
                    except Exception as e:
                        logger.error(f"BlhBlhAdapter: An error occurred during polling: {e}", exc_info=True)
                        # Consider a backoff strategy or re-connection attempt here
                        break

                    await asyncio.sleep(10)

            except httpx.HTTPStatusError as e:
                logger.error(f"BlhBlhAdapter: HTTP Login failed: {e.response.status_code} - {e.response.text}", exc_info=True)
            except socketio.exceptions.ConnectionError as e:
                logger.error(f"BlhBlhAdapter: Socket.IO connection failed: {e}", exc_info=True)
            except Exception as e:
                logger.critical(f"BlhBlhAdapter: An unexpected critical error in connect_and_poll: {e}", exc_info=True)
            finally:
                if self.sio.connected:
                    logger.info("BlhBlhAdapter: Disconnecting Socket.IO client.")
                    await self.sio.disconnect()

            await asyncio.sleep(10)


    

    async def post_messages(self):

        while True:
            post_msg: PostMessage = await self.topic.get()

            text, pic = post_msg.text, post_msg.pic

            initial_pic_data_for_emit = ''

            if pic is not None:
                base64_image = base64.b64encode(pic).decode('utf-8')
                initial_pic_data_for_emit = f'data:image/jpeg;base64,{base64_image}'

                        
            ack_event = asyncio.Event()

            def ack_handler(ack_response_event, data):
                response_data_parsed = AckResult.model_validate(data, by_alias=True)

                logger.info(f"BlhBlhAdapter: Server acknowledged 'postMessage' with: {response_data_parsed}")

                if response_data_parsed.pic_url:
                    upload_headers = {'Content-Type': 'image/jpeg'} # This is usually sufficient

                    try:
                        res = self.http_client.put(str(response_data_parsed.pic_url), content=pic, headers=upload_headers)
                        res.raise_for_status()
                        print('img uploaded')
                    except httpx.RequestError as e:
                        print('error', str(e))

                ack_event.set()
            

            await self.sio_connected_event.wait()
            
            await self.sio.emit(
                event='postMessage', 
                data={
                    'pic': initial_pic_data_for_emit,
                    'text': text,
                },
                callback=ack_handler
            )
            
            await asyncio.wait_for(ack_event.wait(), timeout=10)

    
    def subscribe(self, id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.subscribers[id] = queue
        return queue

    def unsubscribe(self, id: str) -> bool:
        queue = self.subscribers.pop(id, None)
        return queue is not None


    async def _publish(self, msg: Message):
        for subscriber, queue in self.subscribers.items():
            await queue.put(msg)
