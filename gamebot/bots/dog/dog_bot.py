

import asyncio
from gamebot.adapters.blhblh import Message, PostMessage
from gamebot.bots.dog.dog_api import DogImageFetcher
import logging

logger = logging.getLogger(__name__)


class DogBot():

    def __init__(
            self, 
            whitelisted_users: set[str], 
            subscription: asyncio.Queue,
            topic: asyncio.Queue,    
        ) -> None:
        self.dog_api = DogImageFetcher()
        self.whitelisted_users = whitelisted_users
        self.subscription = subscription
        self.topic = topic

    
    async def work(self):
        
        while True:
            msg: Message = await self.subscription.get()
            try:
                if msg.user in self.whitelisted_users and msg.text.startswith('!dog'):

                    if msg.text == '!dog':
                        img = await self.dog_api.fetch_image_bytes()
                        dog = 'dog'
                    else:
                        parts = msg.text.lower().removeprefix('!dog').strip().split()

                        img = await self.dog_api.fetch_image_bytes(*reversed(parts))
                        dog = ' '.join(parts)

                    post_msg = PostMessage(text='Here is a random {}'.format(dog), pic=img)
                    await self.topic.put(post_msg)
            except ConnectionError:
                post_msg = PostMessage(text='Sorry, the dogs are currently out on a walk', pic=None)
                await self.topic.put(post_msg)

    