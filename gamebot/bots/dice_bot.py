import asyncio
import logging
import random

from gamebot.adapters.blhblh import Message, PostMessage

logger = logging.getLogger(__name__)

class DiceBot():
    
    def __init__(self, subscription: asyncio.Queue, topic: asyncio.Queue) -> None:
        self.subscription = subscription
        self.topic = topic

    async def work(self):
        while True:
            msg: Message = await self.subscription.get()

            if msg.text != '!dice':
                continue
            
            roll = random.randint(1, 6)
            logger.info(f'{msg.user} rolled a dice: {roll}')
            post_msg = PostMessage(text=f"Rolling... It's a {roll}", pic=None)
            await self.topic.put(post_msg)
            