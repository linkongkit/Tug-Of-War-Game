import unittest
from src.game.core import Game

class TestGame(unittest.TestCase):

    def setUp(self):
        self.game = Game()

    def test_initial_state(self):
        self.assertEqual(self.game.state, 'waiting')

    def test_start_game(self):
        self.game.start()
        self.assertEqual(self.game.state, 'running')

    def test_end_game(self):
        self.game.start()
        self.game.end()
        self.assertEqual(self.game.state, 'ended')

if __name__ == '__main__':
    unittest.main()