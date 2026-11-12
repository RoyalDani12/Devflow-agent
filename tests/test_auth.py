import os
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from src.telegram.auth import is_authorized_user, require_admin


class AuthTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch("src.telegram.auth.get_stored_admin_id")
    @patch("src.telegram.auth.set_stored_admin_id")
    def test_first_user_claims_ownership(self, mock_set, mock_get):
        mock_get.return_value = None
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(is_authorized_user(12345))
            mock_set.assert_called_once_with(12345)

    @patch("src.telegram.auth.get_stored_admin_id")
    def test_unauthorized_user_is_rejected(self, mock_get):
        mock_get.return_value = 12345
        with patch.dict(os.environ, {"TELEGRAM_ADMIN_ID": "12345"}):
            self.assertTrue(is_authorized_user(12345))
            self.assertFalse(is_authorized_user(99999))

    async def test_require_admin_blocks_unauthorized_user(self):
        dummy_func = AsyncMock()
        decorated = require_admin(dummy_func)

        update = MagicMock()
        update.effective_user.id = 99999
        update.message.reply_text = AsyncMock()

        with patch("src.telegram.auth.is_authorized_user", return_value=False):
            await decorated(update, MagicMock())
            dummy_func.assert_not_called()
            update.message.reply_text.assert_called_once()
            self.assertIn("Access Denied", update.message.reply_text.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
