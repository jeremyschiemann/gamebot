

import asyncio
import itertools
import random
from gamebot.adapters.blhblh import Message, PostMessage
from gamebot.bots.cat.cat_api import CatImageFetcher
import logging

logger = logging.getLogger(__name__)


def unique_cat_permutations_cycle():
    emojis = ['🐱', '🐈', '😺', '🐾', '😻']
    perms = [''.join(p) for p in itertools.permutations(emojis, 4)]
    random.shuffle(perms)
    while True:
        for combo in perms:
            yield combo

emoji_id = unique_cat_permutations_cycle()            


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
                    logger.info(f'{msg.user} requested a cat. ({msg.text})')
                    img = await self.cat_api.fetch_image_bytes()                

                    post_msg = PostMessage(text='Here is a random cat {}'.format(next(emoji_id)), pic=img)
                    await self.topic.put(post_msg)
            except ConnectionError:
                post_msg = PostMessage(text='The cat isnt in the mood to be seen', pic=None)
                await self.topic.put(post_msg)
