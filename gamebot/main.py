# main.py
import asyncio
import os
from pathlib import Path
import sys
import logging
import yaml
import pydantic

from gamebot.adapters.blhblh import BlhBlhAdapter, Message
from gamebot.bots.blackjack.blackjack_bot import BlackjackBot
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


class WhitelistConfig(pydantic.BaseModel):
    whitelisted_users: set[str]


class ConfigModel(pydantic.BaseModel):
    dog_bot: WhitelistConfig
    cat_bot: WhitelistConfig
    blackjack_bot: WhitelistConfig



# --- Main application logic ---
async def main():
    logger.info("Starting BlhBlh Bot Application...")


    username = os.environ.get('blh_user')
    password = os.environ.get('blh_pw')
    
    config_path = Path('/config/config.yaml')
    if not config_path.exists():
        logger.error('config file doesnt exist')

        with config_path.open('w') as f:
            f.write('put config here')

        return
    
    with config_path.open() as config_f:
        config_parsed = yaml.safe_load(config_f)

    try:
        config = ConfigModel.model_validate(config_parsed)
    except pydantic.ValidationError as e:
        logger.error(f'Invalid config: {e}')
        return
    

    if not username or not password:
        logger.error('no user or pw found')
        return

    blhblh_adapter = BlhBlhAdapter(
        username=username,
        password=password
    )


    dog_bot = DogBot(
        whitelisted_users=config.dog_bot.whitelisted_users, 
        subscription=blhblh_adapter.subscribe('DogBot'),
        topic=blhblh_adapter.topic    
    )

    cat_bot = CatBot(
        whitelisted_users=config.cat_bot.whitelisted_users, 
        subscription=blhblh_adapter.subscribe('CatBot'),
        topic=blhblh_adapter.topic    
    )


    log_bot = LogBot(
        subscription=blhblh_adapter.subscribe('LogBot'),
    )

    blackjack_bot = BlackjackBot(
        whitelisted_users=config.blackjack_bot.whitelisted_users,
        subscription=blhblh_adapter.subscribe('Blackjack'),
        topic=blhblh_adapter.topic,
    )


    tasks = {
        'blh_connect': {
            'task': None,
            'coro': blhblh_adapter.reconnect_task,
        },
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
        'blackjack': {
            'task': None,
            'coro': blackjack_bot.work,
        }
    }

    while True:
        for task_name, task_info in tasks.items():
            task = task_info['task']
            if task is None or task.done():
                tasks[task_name]['task'] = asyncio.create_task(task_info['coro']()) 
        
        await asyncio.sleep(10)


# --- Entry point ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SystemExit:
        logger.info("Application exited via signal handler.")
    except Exception as e:
        logger.critical(f"An unhandled critical error occurred during application startup/runtime: {e}", exc_info=True)