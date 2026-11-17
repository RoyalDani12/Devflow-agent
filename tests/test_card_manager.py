import unittest

from src.telegram.card_manager import (
    clear_all_cards,
    create_card,
    get_all_pending_cards,
    get_card,
    get_card_review_keyboard,
    pending_cards,
    pop_card,
)


class CardManagerTests(unittest.TestCase):
    def setUp(self):
        clear_all_cards()

    def test_create_card_registers_and_cleans_text(self):
        text = "📰 **AI DISPATCH**\n⚡ **Model Launch** *breaking*"
        card = create_card(text, category="ai_news")

        self.assertIsNotNone(card.card_id)
        self.assertEqual(card.category, "ai_news")
        self.assertNotIn("*", card.text)
        self.assertEqual(card.status, "pending")
        self.assertIn(card.card_id, pending_cards)

    def test_get_and_pop_card(self):
        card = create_card("Sample card content")
        retrieved = get_card(card.card_id)
        self.assertEqual(retrieved, card)

        popped = pop_card(card.card_id)
        self.assertEqual(popped, card)
        self.assertIsNone(get_card(card.card_id))

    def test_get_all_pending_cards(self):
        c1 = create_card("Card 1")
        c2 = create_card("Card 2")
        all_cards = get_all_pending_cards()
        self.assertEqual(len(all_cards), 2)
        self.assertIn(c1, all_cards)
        self.assertIn(c2, all_cards)

    def test_card_keyboard_contains_card_id(self):
        card = create_card("Card text")
        markup = get_card_review_keyboard(card.card_id)
        buttons = markup.inline_keyboard[0]
        self.assertEqual(len(buttons), 2)
        self.assertEqual(buttons[0].callback_data, f"card:approve:{card.card_id}")
        self.assertEqual(buttons[1].callback_data, f"card:reject:{card.card_id}")

    def tearDown(self):
        clear_all_cards()


if __name__ == "__main__":
    unittest.main()
