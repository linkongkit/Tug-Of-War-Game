class UI:
    def __init__(self):
        pass

    def display_welcome(self):
        print("Welcome to Tug Of War!")

    def display_score(self, player1_score, player2_score):
        print(f"Player 1 Score: {player1_score} | Player 2 Score: {player2_score}")

    def display_winner(self, winner):
        print(f"The winner is: {winner}")

    def clear_screen(self):
        print("\n" * 100)  # Simple way to clear the console screen