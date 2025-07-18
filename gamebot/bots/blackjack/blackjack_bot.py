


import asyncio
from gamebot.adapters.blhblh import Message, PostMessage
import logging

from gamebot.bots.blackjack.blackjack_game import BlackjackGame



class BlackjackBot():

    def __init__(
        self, 
        whitelisted_users: set[str],
        subscription: asyncio.Queue,
        topic: asyncio.Queue,
    ) -> None:
        self.whitelisted_users = whitelisted_users
        self.subscription = subscription
        self.topic = topic
        self.running_games: dict[str, BlackjackGame] = {}


    async def work(self):

        while True:
            msg: Message = await self.subscription.get()

            if msg.user not in self.whitelisted_users or not msg.text.startswith('!blackjack'):
                continue
            
            commands = msg.text.removeprefix('!blackjack').strip().lower()
            current_game = self.running_games.get(msg.user)

            match commands:
                case 'hit' if current_game is not None:
                    state_text = current_game.hit()

                case 'stand' if current_game is not None:
                    state_text = current_game.stand()

                case '' if current_game is not None:
                    state_text = f'You have a running game. Use "!blackjack hit/stand" to play.\n{current_game.status()}'

                case '' if current_game is None:
                    new_game = BlackjackGame()
                    self.running_games[msg.user] = new_game
                    state_text = new_game.status()
                    
                case _:
                    state_text = 'Invalid command. Use "!blackjack" to start a game and "!blackjack hit/stand" to play.'                    


            response_text = f'{msg.name}: {state_text}'

            if current_game is not None and current_game.is_finished():
                self.running_games.pop(msg.user, None)
            post_msg = PostMessage(text=response_text, pic=None)
            await self.topic.put(post_msg)