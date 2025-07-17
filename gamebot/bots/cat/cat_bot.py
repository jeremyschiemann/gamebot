

import asyncio
from gamebot.adapters.blhblh import Message, PostMessage
from gamebot.bots.cat.cat_api import CatImageFetcher
from gamebot.bots.dog.dog_api import DogImageFetcher
import logging

logger = logging.getLogger(__name__)


class CatBot():

    def __init__(
            self, 
            whitelisted_users: set[str], 
            subscription: asyncio.Queue,
            topic: asyncio.Queue,    
        ) -> None:
        self.cat_api = CatImageFetcher()
        self.whitelisted_users = whitelisted_users
        self.subscription = subscription
        self.topic = topic

    
    async def work(self):
        
        while True:
            msg: Message = await self.subscription.get()
            try:

                if msg.user in self.whitelisted_users and msg.text == '!cat':

                    img = await self.cat_api.fetch_image_bytes()                

                    post_msg = PostMessage(text='Here is a random cat', pic=img)
                    await self.topic.put(post_msg)
            except ConnectionError:
                post_msg = PostMessage(text='The cat isnt in the mood to be seen', pic=None)
                await self.topic.put(post_msg)
