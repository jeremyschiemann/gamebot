import asyncio
import logging

logger = logging.getLogger(__name__)

class LogBot():
    
    def __init__(self, subscription: asyncio.Queue) -> None:
        self.subscription = subscription

    
    async def work(self):
        while True:
            msg = await self.subscription.get()
            logger.info(f"{msg.user} said {msg.text}")
            