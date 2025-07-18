# main.py
import asyncio
import os
import sys
import logging

from gamebot.adapters.blhblh import BlhBlhAdapter, Message
from gamebot.bots.cat.cat_bot import CatBot
from gamebot.bots.dog.dog_bot import DogBot
from gamebot.bots.log_bot import LogBot
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# --- Main application logic ---
async def main():
    logger.info("Starting BlhBlh Bot Application...")


    username = os.environ.get('blh_user')
    password = os.environ.get('blh_pw')

    if not username or not password:
        logger.error('no user or pw found')
        return

    blhblh_adapter = BlhBlhAdapter(
        username=username,
        password=password
    )


    dog_bot = DogBot(
        whitelisted_users={
            "Jeremy.is.here",
            "officialtittytoucher"
         }, 
        subscription=blhblh_adapter.subscribe('DogBot'),
        topic=blhblh_adapter.topic    
    )

    cat_bot = CatBot(
        whitelisted_users={
            "Jeremy.is.here",
            "one.sad.potato"
        }, 
        subscription=blhblh_adapter.subscribe('CatBot'),
        topic=blhblh_adapter.topic    
    )


    log_bot = LogBot(
        subscription=blhblh_adapter.subscribe('LogBot'),
    )


    # Start the adapter in a separate task
    #blhblh_task = asyncio.create_task(blhblh_adapter.connect_and_poll())
    #publish_task = asyncio.create_task(blhblh_adapter.post_messages())
    #dog_task = asyncio.create_task(dog_bot.work())
    #cat_task = asyncio.create_task(cat_bot.work())
    #log_task = asyncio.create_task(log_bot.work())

    tasks = {
        'blh': {
            'task': None,
            'coro': blhblh_adapter.connect_and_poll,
        },
        'publish': {
            'task': None,
            'coro': blhblh_adapter.post_messages
        },
        'dog': {
            'task': None,
            'coro': dog_bot.work,
        },
        'cat': {
            'task': None,
            'coro': cat_bot.work,
        },
        'log': {
            'task': None,
            'coro': log_bot.work,
        },
    }

    while True:
        for task_name, task_info in tasks.items():
            task = task_info['task']
            if task is None or task.done():
                tasks[task_name]['task'] = asyncio.create_task(task_info['coro']()) 


# --- Entry point ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SystemExit:
        logger.info("Application exited via signal handler.")
    except Exception as e:
        logger.critical(f"An unhandled critical error occurred during application startup/runtime: {e}", exc_info=True)