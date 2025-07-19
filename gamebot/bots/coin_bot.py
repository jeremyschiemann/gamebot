import asyncio
import logging
import random

from gamebot.adapters.blhblh import Message, PostMessage

logger = logging.getLogger(__name__)

class CoinBot():
    
    def __init__(self, subscription: asyncio.Queue, topic: asyncio.Queue) -> None:
        self.subscription = subscription
        self.topic = topic

    async def work(self):
        while True:
            msg: Message = await self.subscription.get()

            if msg.text != '!coin':
                continue
            
            roll = random.random()

            if roll < 0.499999:
                result =  "It's heads!"
            elif roll < 0.999998:
                result =  "It's tails!"
            else:
                result = 'Omg, it landed on its side 😲'  # 0.0002% chance

            logger.info(f'{msg.user} tossed a coin: {result}')
            post_msg = PostMessage(text=result, pic=None)
            await self.topic.put(post_msg)
            