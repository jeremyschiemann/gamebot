import random

class BlackjackGame:
    def __init__(self):
        self.deck = self._create_deck()
        self.player_hand = []
        self.dealer_hand = []
        self.finished = False
        self.message = ""
        self._deal_initial_cards()

    def _create_deck(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = ranks * 4
        random.shuffle(deck)
        return deck

    def _deal_card(self, hand):
        card = self.deck.pop()
        hand.append(card)

    def _deal_initial_cards(self):
        for _ in range(2):
            self._deal_card(self.player_hand)
            self._deal_card(self.dealer_hand)
        if self._hand_value(self.player_hand) == 21:
            self.finished = True
            self.message = "Blackjack! You win!"

    def _hand_value(self, hand):
        value = 0
        aces = 0
        for card in hand:
            if card in ['J', 'Q', 'K']:
                value += 10
            elif card == 'A':
                aces += 1
                value += 11
            else:
                value += int(card)
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def hit(self):
        if self.finished:
            return "Game is already over."

        self._deal_card(self.player_hand)
        val = self._hand_value(self.player_hand)
        if val > 21:
            self.finished = True
            return self.status() + "\nYou bust! Dealer wins."
        elif val == 21:
            return self.stand()
        return self.status()

    def stand(self):
        if self.finished:
            return "Game is already over."

        # Dealer plays
        while self._hand_value(self.dealer_hand) < 17:
            self._deal_card(self.dealer_hand)

        self.finished = True
        return self._determine_winner()

    def _determine_winner(self):
        player_val = self._hand_value(self.player_hand)
        dealer_val = self._hand_value(self.dealer_hand)

        if dealer_val > 21:
            return self.status() + "\nDealer busts! You win."
        elif dealer_val == player_val:
            return self.status() + "\nPush. It's a tie."
        elif player_val > dealer_val:
            return self.status() + "\nYou win!"
        else:
            return self.status() + "\nDealer wins."

    def status(self):
        player_val = self._hand_value(self.player_hand)
        dealer_card = self.dealer_hand[0] if not self.finished else ", ".join(self.dealer_hand)
        return (
            f"Your hand: {', '.join(self.player_hand)} (Value: {player_val})\n"
            f"Dealer's hand: {dealer_card if not self.finished else f'{dealer_card} (Value: {self._hand_value(self.dealer_hand)})'}"
        )

    def is_finished(self):
        return self.finished

    def has_player_won(self) -> bool | None:
        if not self.finished:
            return None  # Game is not over yet
        player_val = self._hand_value(self.player_hand)
        dealer_val = self._hand_value(self.dealer_hand)
        if player_val > 21:
            return False
        if dealer_val > 21:
            return True
        if player_val > dealer_val:
            return True
        if player_val < dealer_val:
            return False
        return None  # Tie / push