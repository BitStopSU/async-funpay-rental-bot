import asyncio
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call, patch

from aioFunPayAPI.common.enums import OrderStatuses

import admin_menu
import daily_checks
import funpay_bot
import main as app_main
import notify
import password_worker
import profile_verification
import ticker
from config import Config
from database import Database, DuplicateAccountError
from funpay_bot import RentalBot
from funpay_session import FunPayAccount
from i18n import tr
from listing_sync import normalize_funpay_lot_id
from prepare_listing import build_listing_text


class DatabaseFunctionalTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(str(Path(self.temp_dir.name) / "test.db"))

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def add_lot_account(self, *, buyer="buyer", chat_id="chat", hours=2):
        user_id = self.db.get_or_create_user(buyer)
        account_id = self.db.add_account(
            steamid64="76561198000000001",
            dota_account_id="123456",
            mmr=4000,
            behavior_score=9500,
        )
        self.db.register_lot("1001", "Test listing", 2.5, account_id)
        end = self.db.create_rental(
            "order-1", user_id, account_id, "1001", hours, buyer, chat_id
        )
        return user_id, account_id, end

    def test_funpay_lot_id_parser_accepts_supported_link_formats_only(self):
        for value in (
            "80402747",
            "https://funpay.com/lots/offer?id=80402747",
            "https://www.funpay.com/lots/offer/?id=80402747",
            "funpay.com/lots/offer?id=80402747",
            "www.funpay.com/lots/offer?id=80402747",
            "FUNPAY.COM/lots/offer?id=80402747",
            "<https://funpay.com/lots/offer?id=80402747>",
            "https://funpay.com/lots/offer?id=80402747.",
        ):
            with self.subTest(value=value):
                self.assertEqual(normalize_funpay_lot_id(value), "80402747")
        for value in (
            "https://funpay.com.evil.example/lots/offer?id=80402747",
            "https://example.com/lots/offer?id=80402747",
            "https://user@funpay.com/lots/offer?id=80402747",
            "http://funpay.com/lots/offer?id=80402747",
            "https://funpay.com/lots/offer?id=80402747&id=900",
            "https://funpay.com/lots/81/trade",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_funpay_lot_id(value)

    def test_rental_creation_extension_and_expiry_rules(self):
        user_id, account_id, created_end = self.add_lot_account()
        rental = self.db.get_active_rental_by_chat("chat")
        self.assertEqual(rental["order_id"], "order-1")
        self.assertGreaterEqual(
            datetime.fromisoformat(created_end.isoformat()) -
            datetime.fromisoformat(rental["started_at"]),
            timedelta(hours=2, minutes=30) - timedelta(seconds=1),
        )
        self.assertEqual(
            self.db.get_account_listing_data(account_id)["status"], "rented"
        )

        first_extension = self.db.extend_rental(
            "order-1", 3, extension_order_id="extension-1"
        )
        second_extension = self.db.extend_rental(
            "order-1", 3, extension_order_id="extension-1"
        )
        self.assertEqual(first_extension, second_extension)
        self.assertEqual(
            first_extension,
            created_end + timedelta(hours=3),
        )
        self.assertEqual(
            self.db.conn.execute(
                "SELECT quantity FROM rentals WHERE order_id = 'order-1'"
            ).fetchone()[0],
            5,
        )
        self.assertTrue(self.db.is_order_processed("extension-1"))

        self.db.conn.execute(
            "UPDATE rentals SET ends_at = ? WHERE order_id = 'order-1'",
            ((datetime.now() + timedelta(hours=1)).isoformat(),),
        )
        self.assertIsNone(self.db.release_expired_rental("order-1"))
        self.assertEqual(
            self.db.get_active_rental_by_buyer("BUYER")["order_id"], "order-1"
        )

        self.db.conn.execute(
            "UPDATE rentals SET ends_at = ? WHERE order_id = 'order-1'",
            ((datetime.now() - timedelta(seconds=1)).isoformat(),),
        )
        released = self.db.release_expired_rental("order-1")
        self.assertIsNotNone(released)
        self.assertEqual(
            self.db.conn.execute(
                "SELECT status FROM rentals WHERE order_id = 'order-1'"
            ).fetchone()[0],
            "expired",
        )
        self.assertEqual(self.db.get_account_listing_data(account_id)["status"], "free")
        self.assertIsNone(self.db.get_active_rental_by_chat("chat"))
        self.assertTrue(self.db.is_order_processed("order-1"))

    def test_active_buyer_account_and_vac_guards(self):
        _, account_id, _ = self.add_lot_account()
        with self.assertRaises(ValueError):
            self.db.create_rental(
                "another-order", self.db.get_or_create_user("BUYER"),
                account_id, "1001", 1, "BUYER", "chat-2",
            )
        self.assertIsNone(self.db.get_free_account_for_lot("1001"))
        self.assertEqual(self.db.mark_vac_banned("76561198000000001"), 1)
        self.assertEqual(
            self.db.get_account_listing_data(account_id)["status"], "banned"
        )
        self.assertIsNone(self.db.get_free_account(min_mmr=0))
        self.assertEqual(
            self.db.conn.execute(
                "SELECT COUNT(*) FROM logs WHERE event_type = 'account_vac_detected'"
            ).fetchone()[0],
            1,
        )

    def test_available_lots_exclude_rented_and_vac_banned_accounts(self):
        _, available_id, _ = self.add_lot_account(buyer="renter")
        account_id = self.db.add_account(dota_account_id="987654", mmr=3000)
        self.db.register_lot("1002", "Another listing", 3.0, account_id)
        self.db.mark_vac_banned("76561198000000001")
        available = self.db.get_available_lots()
        self.assertEqual([row["lot_id"] for row in available], ["1002"])
        self.db.create_rental(
            "order-2", self.db.get_or_create_user("buyer-2"), account_id,
            "1002", 1, "buyer-2", "chat-2",
        )
        self.assertEqual(self.db.get_available_lots(), [])
        self.assertIsNotNone(available_id)

    def test_late_extension_starts_now_without_expiry_buffer(self):
        _, _, original_end = self.add_lot_account(hours=1)
        expired_at = datetime.now() - timedelta(minutes=10)
        self.db.conn.execute(
            "UPDATE rentals SET ends_at = ? WHERE order_id = 'order-1'",
            (expired_at.isoformat(),),
        )
        before_extension = datetime.now()
        extended_end = self.db.extend_rental(
            "order-1", 2, extension_order_id="late-extension"
        )
        after_extension = datetime.now()
        self.assertGreaterEqual(
            extended_end,
            before_extension + timedelta(hours=2),
        )
        self.assertLessEqual(
            extended_end,
            after_extension + timedelta(hours=2, seconds=1),
        )
        self.assertNotEqual(extended_end, original_end + timedelta(hours=2))
        self.assertIsNone(self.db.release_expired_rental("order-1"))

    def test_extension_payment_request_holds_expiry_without_changing_paid_time(self):
        _, account_id, original_end = self.add_lot_account(hours=1)
        request = self.db.create_extension_request("chat")
        repeated = self.db.create_extension_request("chat")
        self.assertEqual(request["request_id"], repeated["request_id"])
        self.assertEqual(request["expires_at"], repeated["expires_at"])
        self.assertEqual(
            datetime.fromisoformat(
                self.db.get_active_rental_by_chat("chat")["ends_at"]
            ),
            original_end,
        )

        self.db.conn.execute(
            "UPDATE rentals SET ends_at = ? WHERE order_id = 'order-1'",
            ((datetime.now() - timedelta(seconds=1)).isoformat(),),
        )
        self.assertEqual(self.db.get_expired_rentals(), [])
        self.db.conn.execute(
            "UPDATE extension_requests SET expires_at = ? WHERE request_id = ?",
            ((datetime.now() - timedelta(seconds=1)).isoformat(), request["request_id"]),
        )
        self.assertEqual(len(self.db.get_expired_rentals()), 1)
        released = self.db.release_expired_rental("order-1")
        self.assertEqual(released["account_id"], account_id)
        self.assertEqual(
            self.db.conn.execute(
                "SELECT status FROM extension_requests WHERE request_id = ?",
                (request["request_id"],),
            ).fetchone()["status"],
            "expired",
        )

    def test_manual_password_task_and_notification_queue(self):
        _, account_id, _ = self.add_lot_account(hours=1)
        self.db.conn.execute(
            "UPDATE accounts SET auto_change_password = 1 WHERE account_id = ?",
            (account_id,),
        )
        self.db.conn.execute(
            "UPDATE rentals SET ends_at = ? WHERE order_id = 'order-1'",
            ((datetime.now() - timedelta(seconds=1)).isoformat(),),
        )
        self.db.release_expired_rental("order-1")
        task = self.db.get_next_password_task()
        self.assertIsNotNone(task)
        self.assertEqual(task["account_id"], account_id)
        self.assertIn("manual review only", task["note"])

        self.db.queue_notification("warning")
        self.db.queue_notification("urgent", severity="critical")
        warnings = self.db.get_pending_notifications(severity="warning")
        critical = self.db.get_pending_notifications(severity="critical")
        self.assertEqual([row["text"] for row in warnings], ["warning"])
        self.assertEqual([row["text"] for row in critical], ["urgent"])
        self.db.mark_notifications_sent([critical[0]["notification_id"]])
        self.assertEqual(self.db.get_pending_notifications(severity="critical"), [])
        with self.assertRaises(ValueError):
            self.db.queue_notification("invalid", severity="urgent")

    def test_public_statistic_ranges_are_enforced(self):
        account_id = self.db.add_account(dota_account_id="123456")
        self.db.update_mmr(account_id, 15000)
        self.db.update_behavior_score(account_id, 12000)
        for invalid_mmr in (-1, 15001, True, 1.5):
            with self.subTest(mmr=invalid_mmr), self.assertRaises(ValueError):
                self.db.update_mmr(account_id, invalid_mmr)
        for invalid_behavior in (-1, 12001, True, 1.5):
            with self.subTest(behavior=invalid_behavior), self.assertRaises(ValueError):
                self.db.update_behavior_score(account_id, invalid_behavior)

    def test_duplicate_account_ids_are_rejected_on_add_and_edit(self):
        first_id = self.db.add_account(
            steamid64="76561198000000123",
            dota_account_id="123456",
        )
        with self.assertRaises(DuplicateAccountError) as duplicate_dota:
            self.db.add_account(
                steamid64="76561198000000456",
                dota_account_id="123456",
            )
        self.assertEqual(duplicate_dota.exception.existing_account_id, first_id)

        with self.assertRaises(DuplicateAccountError) as duplicate_steam:
            self.db.add_account(
                steamid64="76561198000000123",
                dota_account_id="654321",
            )
        self.assertEqual(duplicate_steam.exception.existing_account_id, first_id)

        second_id = self.db.add_account(dota_account_id="654321")
        with self.assertRaises(DuplicateAccountError) as duplicate_edit:
            self.db.set_dota_account_id(second_id, "123456")
        self.assertEqual(duplicate_edit.exception.existing_account_id, first_id)
        with self.assertRaises(DuplicateAccountError):
            self.db.update_account_public_field(
                second_id, "steamid64", "76561198000000123"
            )
        self.assertEqual(
            self.db.conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0],
            2,
        )

    def test_screenshot_submission_is_idempotent_and_audited(self):
        _, account_id, _ = self.add_lot_account()
        submission = self.db.start_screenshot_submission(
            "order-1", account_id, "buyer", "chat", "message-1"
        )
        self.assertIsNotNone(submission)
        self.assertIsNone(
            self.db.start_screenshot_submission(
                "order-1", account_id, "buyer", "chat", "message-1"
            )
        )
        self.assertTrue(self.db.mark_screenshot_submission_sent(submission, 99, "file"))
        self.assertFalse(
            self.db.mark_screenshot_submission_sent(submission, 99, "file")
        )
        row = self.db.conn.execute(
            """SELECT status, telegram_message_id, telegram_file_id
               FROM screenshot_submissions"""
        ).fetchone()
        self.assertEqual(tuple(row), ("sent", 99, "file"))

    def test_legacy_migration_removes_secrets_and_preserves_relations(self):
        self.db.close()
        legacy_path = Path(self.temp_dir.name) / "legacy.db"
        conn = sqlite3.connect(legacy_path)
        conn.executescript("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                funpay_nick TEXT UNIQUE NOT NULL,
                first_seen TEXT NOT NULL
            );
            CREATE TABLE accounts (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT UNIQUE,
                password_enc BLOB,
                shared_secret_enc BLOB,
                email_login TEXT,
                email_password_enc BLOB,
                steamid64 TEXT,
                dota_account_id TEXT,
                mmr INTEGER,
                behavior_score INTEGER,
                vac_banned INTEGER DEFAULT 0,
                status TEXT DEFAULT 'free',
                auto_change_password INTEGER DEFAULT 0,
                last_check TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE lots (
                lot_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                price_per_hour REAL NOT NULL,
                account_id INTEGER REFERENCES accounts(account_id)
            );
            CREATE TABLE rentals (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id),
                account_id INTEGER NOT NULL REFERENCES accounts(account_id),
                lot_id TEXT NOT NULL REFERENCES lots(lot_id),
                quantity INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                ends_at TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                buyer_nick TEXT NOT NULL
            );
            INSERT INTO users VALUES (1, 'buyer', '2025-01-01');
            INSERT INTO accounts (
                account_id, login, password_enc, shared_secret_enc, email_login,
                email_password_enc, steamid64, dota_account_id, mmr,
                behavior_score, status, created_at
            ) VALUES (
                7, 'LOGIN_MARKER', X'50415353574F52445F4D41524B4552',
                X'5348415245445F4D41524B4552', 'EMAIL_MARKER',
                X'454D41494C5F504153535F4D41524B4552',
                '76561198000000007', '777777', 4500, 9000, 'rented', '2025-01-01'
            );
            INSERT INTO lots VALUES ('7001', 'Legacy listing', 2.5, 7);
            INSERT INTO rentals VALUES (
                'legacy-order', 1, 7, '7001', 2, '2025-01-01',
                '2025-01-02', 'active', 'buyer'
            );
        """)
        conn.commit()
        conn.close()

        migrated = Database(str(legacy_path))
        try:
            columns = {
                row["name"]
                for row in migrated.conn.execute("PRAGMA table_info(accounts)")
            }
            self.assertFalse(columns.intersection({
                "login", "password_enc", "shared_secret_enc",
                "email_login", "email_password_enc",
            }))
            account = migrated.get_account_listing_data(7)
            self.assertEqual(account["dota_account_id"], "777777")
            self.assertEqual(account["mmr"], 4500)
            self.assertEqual(
                migrated.conn.execute(
                    "SELECT account_id FROM rentals WHERE order_id = 'legacy-order'"
                ).fetchone()[0],
                7,
            )
            self.assertEqual(migrated.get_lot("7001")["account_id"], 7)
            self.assertEqual(
                migrated.get_account_listing_data(7)["mmr_source"], "manual"
            )
            self.assertEqual(
                list(migrated.conn.execute("PRAGMA foreign_key_check")), []
            )
        finally:
            migrated.close()
        database_bytes = legacy_path.read_bytes()
        for marker in (
            b"LOGIN_MARKER",
            b"EMAIL_MARKER",
            b"PASSWORD_MARKER",
            b"SHARED_MARKER",
            b"EMAIL_PASS_MARKER",
        ):
            self.assertNotIn(marker, database_bytes)


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class _FakeHttpClient:
    def __init__(
        self, steam_players=None, mmr=4500, rank_tier=None,
        profile_payloads=None,
    ):
        self.steam_players = steam_players or []
        self.mmr = mmr
        self.rank_tier = rank_tier
        self.profile_payloads = profile_payloads or {}
        self.calls = []

    async def get(self, url, params=None):
        self.calls.append((url, params))
        if url == daily_checks.STEAM_BANS_URL:
            return _FakeResponse({"players": self.steam_players})
        dota_id = url.rsplit("/", maxsplit=1)[-1]
        if dota_id in self.profile_payloads:
            return _FakeResponse(self.profile_payloads[dota_id])
        return _FakeResponse({
            "mmr_estimate": {"estimate": self.mmr},
            "rank_tier": self.rank_tier,
        })

    async def aclose(self):
        return None


class _FailingHttpClient(_FakeHttpClient):
    async def get(self, url, params=None):
        self.calls.append((url, params))
        raise daily_checks.httpx.ConnectError("mocked offline")


class _ProfileResponse:
    def __init__(self, *, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self.payload = payload
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ValueError("mocked HTTP failure")

    def json(self):
        return self.payload


class _ProfileClient:
    def __init__(self, opendota, dotabuff, steam=None):
        self.opendota = opendota
        self.dotabuff = dotabuff
        self.steam = steam
        self.calls = []

    async def get(self, url, params=None):
        self.calls.append((url, params))
        if "api.opendota.com" in url:
            return self.opendota
        if "api.steampowered.com" in url:
            return self.steam
        return self.dotabuff


class AsyncFunctionalTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        asyncio.get_running_loop().slow_callback_duration = 1
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(str(Path(self.temp_dir.name) / "test.db"))

    async def asyncTearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def add_account_with_lot(self, buyer="buyer", chat_id="chat"):
        user_id = self.db.get_or_create_user(buyer)
        account_id = self.db.add_account(
            steamid64="76561198000000011",
            dota_account_id="222222",
            mmr=4000,
            behavior_score=9800,
        )
        self.db.register_lot("2001", "Test listing", 3.0, account_id)
        self.db.create_rental(
            "order-main", user_id, account_id, "2001", 1, buyer, chat_id
        )
        return account_id

    async def test_daily_checks_batches_vac_and_updates_mmr(self):
        for index in range(101):
            self.db.add_account(steamid64=str(76561198000010000 + index))
        mmr_account = self.db.add_account(
            steamid64="76561198000099999",
            dota_account_id="333333",
            mmr=1000,
        )
        self.db.add_account(
            steamid64="76561198000099998",
            dota_account_id="444444",
            mmr=1000,
        )

        steam_players = [{
            "SteamId": "76561198000010000",
            "VACBanned": True,
        }]
        client = _FakeHttpClient(steam_players=steam_players, mmr=5000)
        callback = AsyncMock()
        with (
            patch.object(Config, "STEAM_API_KEY", "test-key"),
            patch.object(Config, "OPENDOTA_REQUEST_DELAY", 0),
        ):
            await daily_checks.run_daily_checks(self.db, client, callback)

        steam_calls = [
            call for call in client.calls
            if call[0] == daily_checks.STEAM_BANS_URL
        ]
        self.assertEqual(len(steam_calls), 2)
        self.assertEqual(
            [len(call[1]["steamids"].split(",")) for call in steam_calls],
            [100, 3],
        )
        self.assertEqual(
            self.db.conn.execute(
                "SELECT status FROM accounts WHERE steamid64 = '76561198000010000'"
            ).fetchone()[0],
            "banned",
        )
        self.assertEqual(
            self.db.get_account_listing_data(mmr_account)["mmr"],
            5000,
        )
        self.assertEqual(callback.await_count, 2)
        self.assertIn(
            call(mmr_account),
            callback.await_args_list,
        )
        self.assertEqual(
            len([call for call in client.calls if "api.opendota.com" in call[0]]),
            2,
        )

    async def test_daily_checks_without_steam_key_still_update_mmr(self):
        self.db.add_account(
            steamid64="76561198000123456",
            dota_account_id="555555",
            mmr=2500,
        )
        client = _FakeHttpClient(mmr=2600)
        with (
            patch.object(Config, "STEAM_API_KEY", None),
            patch.object(Config, "OPENDOTA_REQUEST_DELAY", 0),
        ):
            await daily_checks.run_daily_checks(self.db, client)
        self.assertEqual(
            [url for url, _ in client.calls],
            [daily_checks.OPENDOTA_PLAYER_URL.format("555555")],
        )
        self.assertEqual(
            self.db.conn.execute(
                "SELECT mmr FROM accounts"
            ).fetchone()[0],
            2600,
        )
        self.assertEqual(
            self.db.get_pending_notifications(severity="warning")[0]["text"],
            tr("notify_vac_disabled"),
        )

    async def test_rank_tier_is_approximate_mmr_fallback_only(self):
        approximate_account = self.db.add_account(
            dota_account_id="555557",
            mmr=1000,
        )
        exact_account = self.db.add_account(
            dota_account_id="555558",
            mmr=2000,
        )
        client = _FakeHttpClient(profile_payloads={
            "555557": {
                "mmr_estimate": {"estimate": None},
                "rank_tier": 63,
            },
            "555558": {
                "mmr_estimate": {"estimate": 4200},
                "rank_tier": 63,
            },
        })
        with (
            patch.object(Config, "STEAM_API_KEY", None),
            patch.object(Config, "OPENDOTA_REQUEST_DELAY", 0),
        ):
            await daily_checks.run_daily_checks(self.db, client)

        approximate = self.db.get_account_listing_data(approximate_account)
        self.assertEqual(approximate["mmr"], 4158)
        self.assertEqual(approximate["mmr_source"], "rank_tier_approx")
        title, description = build_listing_text(approximate, 3.0)
        self.assertIn("~4158", title)
        self.assertIn("~4158", description)
        self.assertIn("MMR: ~4158", admin_menu._accounts_text(self.db))

        exact = self.db.get_account_listing_data(exact_account)
        self.assertEqual(exact["mmr"], 4200)
        self.assertEqual(exact["mmr_source"], "opendota_estimate")
        log = self.db.conn.execute(
            """SELECT details, severity FROM logs
               WHERE event_type = 'account_mmr_checked'
                 AND account_id = ? ORDER BY log_id DESC LIMIT 1""",
            (approximate_account,),
        ).fetchone()
        self.assertEqual(json.loads(log["details"])["source"], "rank_tier_approx")
        self.assertEqual(log["severity"], "warning")

    async def test_rank_tier_mmr_table_rejects_unsupported_values(self):
        expected = {
            11: 0,
            25: 1386,
            43: 2618,
            63: 4158,
            75: 5420,
        }
        for rank_tier, mmr in expected.items():
            with self.subTest(rank_tier=rank_tier):
                self.assertEqual(
                    daily_checks.estimate_mmr_from_rank_tier(rank_tier), mmr
                )
        for rank_tier in (None, 0, 10, 16, 80, 85, "invalid", True):
            with self.subTest(rank_tier=rank_tier):
                self.assertIsNone(
                    daily_checks.estimate_mmr_from_rank_tier(rank_tier)
                )

    async def test_daily_check_api_failures_are_audited_and_queued(self):
        self.db.add_account(
            steamid64="76561198000123457",
            dota_account_id="555556",
            mmr=2500,
        )
        client = _FailingHttpClient()
        with (
            patch.object(Config, "STEAM_API_KEY", "test-key"),
            patch.object(Config, "OPENDOTA_REQUEST_DELAY", 0),
            patch.object(daily_checks.logger, "error"),
        ):
            await daily_checks.run_daily_checks(self.db, client)
        failures = self.db.conn.execute(
            """SELECT event_type FROM logs
               WHERE event_type IN ('vac_check_failed', 'mmr_check_failed')
               ORDER BY event_type"""
        ).fetchall()
        self.assertEqual(
            [row["event_type"] for row in failures],
            ["mmr_check_failed", "vac_check_failed"],
        )
        self.assertEqual(
            len(self.db.get_pending_notifications(severity="warning")),
            2,
        )

    async def test_funpay_paid_order_extension_duplicate_and_guard_request(self):
        account_id = self.db.add_account(
            steamid64="76561198000000021",
            dota_account_id="888888",
            mmr=3500,
        )
        self.db.register_lot("3001", "Rental listing", 2.0, account_id)
        self.db.conn.execute(
            """INSERT INTO lots
               (lot_id, title, title_en, price_per_hour, is_extension, account_id)
               VALUES ('3002', 'Extension', 'Extension', 1.0, 1, NULL)"""
        )
        self.db.conn.commit()
        bot = RentalBot("not-used", self.db)
        bot.acc = SimpleNamespace(
            id=999,
            get_order=AsyncMock(return_value=SimpleNamespace(short_description=None)),
            send_message=AsyncMock(),
        )
        order = SimpleNamespace(
            id="#sale-1",
            status=OrderStatuses.PAID,
            buyer_username="buyer",
            buyer_id=12345,
            chat_id=67890,
            amount=2,
            lot_id="3001",
        )
        event = SimpleNamespace(order=order)
        await bot.on_new_order(event)
        rental = self.db.get_active_rental_by_buyer("buyer")
        self.assertIsNotNone(rental)
        self.assertEqual(rental["order_id"], "sale-1")
        self.assertEqual(rental["chat_id"], "67890")
        self.assertEqual(rental["quantity"], 2)
        bot.acc.send_message.assert_awaited_once()

        original_end = datetime.fromisoformat(rental["ends_at"])
        extension_order = SimpleNamespace(
            id="extension-sale",
            status=OrderStatuses.PAID,
            buyer_username="buyer",
            buyer_id=12345,
            chat_id=67890,
            amount=4,
            lot_id="3002",
        )
        await bot.on_new_order(SimpleNamespace(order=extension_order))
        extended_end = datetime.fromisoformat(
            self.db.get_active_rental_by_buyer("buyer")["ends_at"]
        )
        self.assertEqual(extended_end, original_end + timedelta(hours=4))
        self.assertTrue(self.db.is_order_processed("extension-sale"))

        self.db.conn.execute(
            "UPDATE rentals SET ends_at = ? WHERE order_id = 'sale-1'",
            ((datetime.now() - timedelta(minutes=5)).isoformat(),),
        )
        late_extension = SimpleNamespace(
            id="extension-late",
            status=OrderStatuses.PAID,
            buyer_username="buyer",
            buyer_id=12345,
            chat_id=67890,
            amount=1,
            lot_id="3002",
        )
        before_late_extension = datetime.now()
        await bot.on_new_order(SimpleNamespace(order=late_extension))
        late_end = datetime.fromisoformat(
            self.db.get_active_rental_by_buyer("buyer")["ends_at"]
        )
        self.assertGreaterEqual(
            late_end,
            before_late_extension + timedelta(hours=1),
        )
        self.assertTrue(self.db.is_order_processed("extension-late"))

        await bot.on_new_order(event)
        self.assertEqual(
            self.db.conn.execute("SELECT COUNT(*) FROM rentals").fetchone()[0],
            1,
        )

        message = SimpleNamespace(
            author_id=12345,
            chat_id=67890,
            text="!код",
            image_link=None,
        )
        await bot.on_message(SimpleNamespace(message=message))
        self.assertEqual(bot.acc.send_message.await_count, 5)
        self.assertEqual(
            self.db.conn.execute(
                """SELECT COUNT(*) FROM logs
                   WHERE event_type = 'credential_request_referred_to_operator'"""
            ).fetchone()[0],
            1,
        )

    async def test_akk_lists_available_lots_and_returns_selected_link(self):
        self.db.add_account(
            dota_account_id="987654", mmr=3200, behavior_score=9500
        )
        self.db.register_lot("3003", "Available listing", 2.5, 1)
        bot = RentalBot("not-used", self.db)
        bot.acc = SimpleNamespace(id=999, send_message=AsyncMock())
        for text in ("/akk", "/akk 3003"):
            message = SimpleNamespace(
                author_id=12345, chat_id=67890, text=text, image_link=None
            )
            await bot.on_message(SimpleNamespace(message=message))
        self.assertIn("/akk <ID_лота>", bot.acc.send_message.await_args_list[0].args[1])
        self.assertIn(
            "https://funpay.com/lots/offer?id=3003",
            bot.acc.send_message.await_args_list[1].args[1],
        )
        self.assertEqual(
            self.db.conn.execute(
                """SELECT COUNT(*) FROM logs
                   WHERE event_type IN (
                       'available_lots_requested', 'available_lot_selected'
                   )"""
            ).fetchone()[0],
            2,
        )

    async def test_dodep_opens_fixed_window_and_sends_listing_link(self):
        self.add_account_with_lot()
        bot = RentalBot("not-used", self.db)
        bot.acc = SimpleNamespace(id=999, send_message=AsyncMock())
        message = SimpleNamespace(
            author_id=12345, chat_id="chat", text="/dodep", image_link=None
        )
        with patch.object(Config, "EXTENSION_PAYMENT_WINDOW_MINUTES", 10):
            await bot.on_message(SimpleNamespace(message=message))
            await bot.on_message(SimpleNamespace(message=message))
        self.assertEqual(bot.acc.send_message.await_count, 2)
        self.assertIn(
            "https://funpay.com/lots/offer?id=2001",
            bot.acc.send_message.await_args_list[0].args[1],
        )
        requests = self.db.conn.execute(
            "SELECT * FROM extension_requests WHERE status = 'pending'"
        ).fetchall()
        self.assertEqual(len(requests), 1)

    async def test_paid_order_from_dodep_link_extends_only_after_payment(self):
        self.add_account_with_lot()
        rental = self.db.get_active_rental_by_chat("chat")
        original_end = datetime.fromisoformat(rental["ends_at"])
        self.db.create_extension_request("chat")
        bot = RentalBot("not-used", self.db)
        bot.acc = SimpleNamespace(
            get_order=AsyncMock(return_value=SimpleNamespace(short_description=None)),
            send_message=AsyncMock(),
        )
        order = SimpleNamespace(
            id="paid-extension",
            status=OrderStatuses.PAID,
            buyer_username="buyer",
            buyer_id=12345,
            chat_id="chat",
            amount=2,
            lot_id="2001",
        )
        await bot.on_new_order(SimpleNamespace(order=order))
        updated = self.db.get_active_rental_by_chat("chat")
        self.assertEqual(
            datetime.fromisoformat(updated["ends_at"]),
            original_end + timedelta(hours=2),
        )
        self.assertEqual(
            tuple(self.db.conn.execute(
                """SELECT status, extension_order_id FROM extension_requests"""
            ).fetchone()),
            ("paid", "paid-extension"),
        )

    async def test_late_dodep_payment_goes_to_operator_not_new_rental(self):
        self.add_account_with_lot()
        request = self.db.create_extension_request("chat")
        self.db.conn.execute(
            "UPDATE rentals SET ends_at = ? WHERE order_id = 'order-main'",
            ((datetime.now() - timedelta(minutes=11)).isoformat(),),
        )
        self.db.conn.execute(
            "UPDATE extension_requests SET expires_at = ? WHERE request_id = ?",
            ((datetime.now() - timedelta(minutes=1)).isoformat(), request["request_id"]),
        )
        self.assertIsNotNone(self.db.release_expired_rental("order-main"))
        bot = RentalBot("not-used", self.db)
        bot.acc = SimpleNamespace(
            get_order=AsyncMock(return_value=SimpleNamespace(short_description=None)),
            send_message=AsyncMock(),
        )
        order = SimpleNamespace(
            id="late-paid-extension",
            status=OrderStatuses.PAID,
            buyer_username="buyer",
            buyer_id=12345,
            chat_id="chat",
            amount=1,
            lot_id="2001",
        )
        await bot.on_new_order(SimpleNamespace(order=order))
        self.assertEqual(
            self.db.conn.execute("SELECT COUNT(*) FROM rentals").fetchone()[0],
            1,
        )
        self.assertEqual(
            self.db.conn.execute(
                """SELECT COUNT(*) FROM logs
                   WHERE event_type = 'late_extension_payment_referred'"""
            ).fetchone()[0],
            1,
        )

    async def test_funpay_lot_form_parser_accepts_html_response(self):
        class FakeResponse:
            text = """
                <form>
                  <input name="offer_id" value="123">
                  <input name="price" value="4.5">
                  <input type="checkbox" name="active" checked>
                  <input name="amount" value="1">
                  <textarea name="fields[summary][ru]">Title</textarea>
                  <textarea name="fields[summary][en]">Title</textarea>
                  <textarea name="fields[desc][ru]">Description</textarea>
                  <textarea name="fields[desc][en]">Description</textarea>
                  <select name="fields[type]">
                    <option value="1" selected>Rent</option>
                  </select>
                </form>
            """

            def json(self):
                raise json.JSONDecodeError("FunPay returned HTML", "", 0)

        account = FunPayAccount(golden_key="not-used")
        account._Account__initiated = True
        with patch.object(
            account, "method", new_callable=AsyncMock,
            return_value=FakeResponse(),
        ) as request:
            fields = await account.get_lot_fields(123)
        request.assert_awaited_once()
        self.assertEqual(fields.title_ru, "Title")
        self.assertEqual(fields.price, 4.5)
        self.assertTrue(fields.active)
        self.assertEqual(fields.fields["fields[type]"], "1")

    async def test_unpaid_funpay_order_is_ignored(self):
        bot = RentalBot("not-used", self.db)
        bot.acc = SimpleNamespace(get_order=AsyncMock())
        order = SimpleNamespace(id="unpaid", status=object())
        await bot.on_new_order(SimpleNamespace(order=order))
        bot.acc.get_order.assert_not_awaited()
        self.assertEqual(
            self.db.conn.execute("SELECT COUNT(*) FROM rentals").fetchone()[0],
            0,
        )

    async def test_screenshot_url_validation_and_admin_delivery(self):
        account_id = self.add_account_with_lot()
        bot = RentalBot("not-used", self.db)
        bot.acc = SimpleNamespace(id=999, send_message=AsyncMock())
        invalid_message = SimpleNamespace(
            author_id=12345, chat_id="chat", text="", id="bad-image",
            image_link="http://attacker.example/image.png",
        )
        with (
            patch.object(Config, "TG_BOT_TOKEN", "test-token"),
            patch.object(Config, "TG_ADMIN_ID", 42),
            patch.object(
                funpay_bot, "send_tg_photo", new_callable=AsyncMock
            ) as send_photo,
        ):
            await bot.on_message(SimpleNamespace(message=invalid_message))
            send_photo.assert_not_awaited()
            self.assertEqual(
                self.db.conn.execute(
                    "SELECT COUNT(*) FROM screenshot_submissions"
                ).fetchone()[0],
                0,
            )

            valid_message = SimpleNamespace(
                author_id=12345, chat_id="chat", text="", id="image-1",
                image_link="https://images.funpay.com/profile.png",
            )
            send_photo.return_value = {
                "message_id": 123,
                "photo": [{"file_id": "telegram-file"}],
            }
            await bot.on_message(SimpleNamespace(message=valid_message))
            send_photo.assert_awaited_once()
            row = self.db.conn.execute(
                """SELECT account_id, status, telegram_message_id, telegram_file_id
                   FROM screenshot_submissions"""
            ).fetchone()
            self.assertEqual(
                tuple(row), (account_id, "sent", 123, "telegram-file")
            )

    async def test_admin_authorization_and_account_creation_flow(self):
        admin_id = 4242
        bot = SimpleNamespace(sync_account_listing=AsyncMock())
        pending = {"action": "new_account"}
        client = object()
        with (
            patch.object(Config, "TG_ADMIN_ID", admin_id),
            patch.object(admin_menu, "_send_text", new_callable=AsyncMock) as send,
            patch.object(
                admin_menu,
                "verify_dota_profile",
                new_callable=AsyncMock,
                return_value=profile_verification.DotaProfileVerification(
                    "found", "unknown"
                ),
            ) as verify,
        ):
            unauthorized = {
                "message": {
                    "from": {"id": 111},
                    "chat": {"id": 111},
                    "text": "123456 4000 9000",
                }
            }
            await admin_menu._handle_update(
                client, self.db, unauthorized, bot, pending
            )
            self.assertEqual(
                self.db.conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0],
                0,
            )

            authorized = {
                "message": {
                    "from": {"id": admin_id},
                    "chat": {"id": admin_id},
                    "text": "123456 4000 9000",
                }
            }
            await admin_menu._handle_update(
                client, self.db, authorized, bot, pending
            )
            verify.assert_awaited_once_with("123456")
        account = self.db.conn.execute(
            """SELECT dota_account_id, mmr, behavior_score
               FROM accounts"""
        ).fetchone()
        self.assertEqual(tuple(account), ("123456", 4000, 9000))
        self.assertFalse(pending)
        bot.sync_account_listing.assert_not_awaited()

    async def test_unverified_dota_profile_is_not_added(self):
        admin_id = 4343
        pending = {"action": "new_account"}
        client = object()

        def update(text):
            return {
                "message": {
                    "from": {"id": admin_id},
                    "chat": {"id": admin_id},
                    "text": text,
                }
            }

        with (
            patch.object(Config, "TG_ADMIN_ID", admin_id),
            patch.object(admin_menu, "_telegram_call", new_callable=AsyncMock),
            patch.object(admin_menu, "_send_text", new_callable=AsyncMock) as send,
            patch.object(
                admin_menu,
                "verify_dota_profile",
                new_callable=AsyncMock,
                return_value=profile_verification.DotaProfileVerification(
                    "not_found", "unknown"
                ),
            ),
        ):
            await admin_menu._handle_update(
                client, self.db, update("123457 4000"), pending=pending
            )
            self.assertEqual(pending["action"], "new_account")
            self.assertEqual(
                self.db.conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0],
                0,
            )
            self.assertIn("не нашёл профиль", send.await_args.args[1])
            self.assertEqual(
                self.db.conn.execute(
                    """SELECT COUNT(*) FROM logs
                       WHERE event_type = 'dota_profile_verification_rejected'"""
                ).fetchone()[0],
                1,
            )

    async def test_duplicate_dota_profile_is_rejected_before_external_verification(self):
        admin_id = 4344
        existing_id = self.db.add_account(dota_account_id="123457")
        pending = {"action": "new_account"}
        update = {
            "message": {
                "from": {"id": admin_id},
                "chat": {"id": admin_id},
                "text": "123457",
            }
        }
        with (
            patch.object(Config, "TG_ADMIN_ID", admin_id),
            patch.object(
                admin_menu, "_send_text", new_callable=AsyncMock
            ) as send,
            patch.object(
                admin_menu, "verify_dota_profile", new_callable=AsyncMock
            ) as verify,
        ):
            await admin_menu._handle_update(
                object(), self.db, update, pending=pending
            )

        verify.assert_not_awaited()
        self.assertIn(f"№{existing_id}", send.await_args.args[1])
        self.assertEqual(
            self.db.conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0],
            1,
        )
        self.assertEqual(pending["action"], "new_account")
        self.assertEqual(
            self.db.conn.execute(
                """SELECT COUNT(*) FROM logs
                   WHERE event_type = 'duplicate_account_rejected'"""
            ).fetchone()[0],
            1,
        )

    async def test_unavailable_opendota_does_not_allow_manual_account_creation(self):
        admin_id = 4444
        pending = {"action": "new_account"}
        client = object()
        update = {
            "message": {
                "from": {"id": admin_id},
                "chat": {"id": admin_id},
                "text": "123459",
            }
        }
        with (
            patch.object(Config, "TG_ADMIN_ID", admin_id),
            patch.object(admin_menu, "_send_text", new_callable=AsyncMock) as send,
            patch.object(
                admin_menu,
                "verify_dota_profile",
                new_callable=AsyncMock,
                return_value=profile_verification.DotaProfileVerification(
                    "unknown", "found"
                ),
            ),
        ):
            await admin_menu._handle_update(
                client, self.db, update, pending=pending
            )
        self.assertEqual(
            self.db.conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0],
            0,
        )
        self.assertIn("OpenDota", send.await_args.args[1])

    async def test_profile_verification_accepts_exact_public_profiles_only(self):
        client = _ProfileClient(
            _ProfileResponse(payload={"profile": {"account_id": 123456}}),
            _ProfileResponse(
                text=(
                    '<html><head><link rel="canonical" '
                    'href="https://www.dotabuff.com/players/123456"></head></html>'
                )
            ),
        )
        with patch.object(profile_verification.Config, "STEAM_API_KEY", None):
            result = await profile_verification.verify_dota_profile(
                "123456", client
            )
        self.assertEqual(result.verified_by, ["OpenDota", "Dotabuff"])
        self.assertEqual(len(client.calls), 2)

        unknown_client = _ProfileClient(
            _ProfileResponse(payload={"profile": None}),
            _ProfileResponse(text="<html><title>Welcome</title></html>"),
        )
        unknown = await profile_verification.verify_dota_profile(
            "123456", unknown_client
        )
        self.assertEqual(unknown.opendota, profile_verification.NOT_FOUND)
        self.assertEqual(unknown.dotabuff, profile_verification.UNKNOWN)
        self.assertEqual(unknown.verified_by, [])
        with self.assertRaises(ValueError):
            await profile_verification.verify_dota_profile("0", unknown_client)

    async def test_profile_verification_uses_steam_api_for_visibility(self):
        dota_id = "123456"
        steamid64 = str(
            profile_verification.STEAM_ID_BASE + int(dota_id)
        )
        for visibility, expected in (
            (1, "private"),
            (2, "friends_only"),
            (3, "public"),
        ):
            with self.subTest(visibility=visibility):
                client = _ProfileClient(
                    _ProfileResponse(
                        payload={
                            "profile": {
                                "account_id": int(dota_id),
                                "steamid": steamid64,
                            },
                            "mmr_estimate": {"estimate": 4200},
                            "rank_tier": 51,
                        }
                    ),
                    _ProfileResponse(text="<html></html>"),
                    _ProfileResponse(
                        payload={
                            "response": {
                                "players": [
                                    {
                                        "steamid": steamid64,
                                        "communityvisibilitystate": visibility,
                                        "personaname": "Public test name",
                                    }
                                ]
                            }
                        }
                    ),
                )
                with patch.object(
                    profile_verification.Config,
                    "STEAM_API_KEY",
                    "test-key",
                ):
                    result = await profile_verification.verify_dota_profile(
                        dota_id, client
                    )
                self.assertEqual(result.opendota, profile_verification.FOUND)
                self.assertEqual(result.steamid64, steamid64)
                self.assertEqual(result.steam_visibility, expected)
                self.assertEqual(result.persona_name, "Public test name")
                self.assertEqual(result.mmr_estimate, 4200)
                self.assertEqual(result.rank_tier, 51)
                self.assertEqual(
                    client.calls[-1],
                    (
                        profile_verification.STEAM_SUMMARIES_URL,
                        {"key": "test-key", "steamids": steamid64},
                    ),
                )

    async def test_admin_link_and_edit_callbacks_follow_pending_states(self):
        admin_id = 5151
        account_id = self.db.add_account(dota_account_id="987654", mmr=3000)
        bot = SimpleNamespace(
            register_listing=AsyncMock(return_value="4001"),
            sync_account_listing=AsyncMock(return_value=False),
        )
        pending = {"action": "link_account", "lot_id": "4001"}
        client = object()

        def callback(data):
            return {
                "callback_query": {
                    "id": "callback",
                    "from": {"id": admin_id},
                    "message": {"chat": {"id": admin_id}},
                    "data": data,
                }
            }

        with (
            patch.object(Config, "TG_ADMIN_ID", admin_id),
            patch.object(admin_menu, "_telegram_call", new_callable=AsyncMock),
            patch.object(admin_menu, "_send_text", new_callable=AsyncMock),
        ):
            link_message = {
                "message": {
                    "from": {"id": admin_id},
                    "chat": {"id": admin_id},
                    "text": "https://funpay.com/lots/offer?id=4001",
                }
            }
            pending["action"] = "lot_id"
            await admin_menu._handle_update(
                client, self.db, link_message, bot, pending
            )
            self.assertEqual(pending["lot_id"], "4001")
            self.assertEqual(pending["action"], "link_account")

            await admin_menu._handle_update(
                client, self.db, callback(f"admin:link_account:{account_id}"),
                bot, pending,
            )
            bot.register_listing.assert_awaited_once_with("4001", account_id)
            self.assertFalse(pending)

            await admin_menu._handle_update(
                client, self.db,
                callback(f"admin:account_field:{account_id}:mmr"),
                bot, pending,
            )
            self.assertEqual(pending["action"], "account_field")
            message = {
                "message": {
                    "from": {"id": admin_id},
                    "chat": {"id": admin_id},
                    "text": "4200",
                }
            }
            await admin_menu._handle_update(client, self.db, message, bot, pending)

        self.assertEqual(self.db.get_account_listing_data(account_id)["mmr"], 4200)
        self.assertFalse(pending)
        bot.sync_account_listing.assert_awaited_once_with(account_id)

    async def test_settings_render_in_both_languages_without_secret_setting(self):
        with patch.object(Config, "BOT_LANGUAGE", "ru"):
            russian = admin_menu._settings_text()
        with patch.object(Config, "BOT_LANGUAGE", "en"):
            english = admin_menu._settings_text()
        self.assertIn("Язык: ru", russian)
        self.assertIn("Language: en", english)
        self.assertNotIn("SECRET_KEY", russian)
        self.assertNotIn("SECRET_KEY", english)

    async def test_notification_delivery_marks_sent_only_after_success(self):
        self.db.queue_notification("urgent", severity="critical")
        row = self.db.get_pending_notifications(severity="critical")[0]
        with (
            patch.object(Config, "TG_BOT_TOKEN", "test-token"),
            patch.object(Config, "TG_ADMIN_ID", 42),
            patch.object(notify, "critical", new_callable=AsyncMock) as send,
            patch.object(notify.logger, "error"),
        ):
            send.side_effect = RuntimeError("offline")
            with patch.object(notify.asyncio, "sleep", new_callable=AsyncMock) as sleep:
                sleep.side_effect = asyncio.CancelledError
                with self.assertRaises(asyncio.CancelledError):
                    await notify.critical_notification_loop(self.db)
        self.assertEqual(
            len(self.db.get_pending_notifications(severity="critical")),
            1,
        )
        self.assertEqual(row["text"], "urgent")

    async def test_critical_notification_success_is_marked_sent(self):
        self.db.queue_notification("urgent", severity="critical")
        with (
            patch.object(Config, "TG_BOT_TOKEN", "test-token"),
            patch.object(Config, "TG_ADMIN_ID", 42),
            patch.object(notify, "critical", new_callable=AsyncMock) as send,
            patch.object(notify.asyncio, "sleep", new_callable=AsyncMock) as sleep,
        ):
            sleep.side_effect = asyncio.CancelledError
            with self.assertRaises(asyncio.CancelledError):
                await notify.critical_notification_loop(self.db)
        send.assert_awaited_once_with("urgent")
        self.assertEqual(
            self.db.get_pending_notifications(severity="critical"),
            [],
        )

    async def test_warning_digest_marks_sent_only_after_success(self):
        self.db.queue_notification("warning")
        with (
            patch.object(Config, "TG_BOT_TOKEN", "test-token"),
            patch.object(Config, "TG_ADMIN_ID", 42),
            patch.object(notify, "send_tg", new_callable=AsyncMock) as send,
            patch.object(notify.asyncio, "sleep", new_callable=AsyncMock) as sleep,
        ):
            sleep.side_effect = [None, asyncio.CancelledError]
            with self.assertRaises(asyncio.CancelledError):
                await notify.digest_loop(self.db)
        send.assert_awaited_once()
        self.assertEqual(
            self.db.get_pending_notifications(severity="warning"),
            [],
        )

    async def test_password_worker_only_notifies_manual_task(self):
        account_id = self.db.add_account(dota_account_id="123123")
        task_id = self.db.queue_password_task(account_id, "manual-only")
        with (
            patch("password_worker.send_tg", new_callable=AsyncMock) as send,
            patch("password_worker.asyncio.sleep", new_callable=AsyncMock) as sleep,
        ):
            sleep.side_effect = asyncio.CancelledError
            with self.assertRaises(asyncio.CancelledError):
                await password_worker.password_worker(self.db)
        send.assert_awaited_once()
        task = self.db.conn.execute(
            "SELECT status, note FROM password_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        self.assertEqual(tuple(task), ("notified", "manual-only"))

    async def test_expiry_ticker_releases_expired_rental(self):
        account_id = self.add_account_with_lot()
        self.db.conn.execute(
            "UPDATE rentals SET ends_at = ? WHERE order_id = 'order-main'",
            ((datetime.now() - timedelta(seconds=1)).isoformat(),),
        )
        with patch.object(ticker.asyncio, "sleep", new_callable=AsyncMock) as sleep:
            sleep.side_effect = asyncio.CancelledError
            with self.assertRaises(asyncio.CancelledError):
                await ticker.expiry_ticker(self.db)
        self.assertEqual(
            self.db.conn.execute(
                "SELECT status FROM rentals WHERE order_id = 'order-main'"
            ).fetchone()[0],
            "expired",
        )
        self.assertEqual(self.db.get_account_listing_data(account_id)["status"], "free")

    async def test_existing_listing_link_and_price_update_use_mock_funpay(self):
        account_id = self.db.add_account(
            dota_account_id="543210", mmr=3800, behavior_score=9600
        )

        class FakeFields:
            title_ru = "Existing listing"
            title_en = "Existing listing"
            price = 4.0
            fields = {}

            def edit_fields(self, values):
                self.fields.update(values)

        fields = FakeFields()
        fake_account = SimpleNamespace(
            get_lot_fields=AsyncMock(return_value=fields),
            save_lot=AsyncMock(),
        )
        bot = RentalBot("not-used", self.db)
        bot.acc = fake_account
        bot._ready.set()
        with patch.object(
            funpay_bot, "sync_listing", new_callable=AsyncMock, return_value=True
        ) as sync:
            self.assertEqual(await bot.register_listing("4001", account_id), "4001")
            registered = self.db.get_lot("4001")
            self.assertEqual(registered["account_id"], account_id)
            self.assertEqual(registered["price_per_hour"], 4.0)
            self.assertTrue(await bot.update_listing_price("4001", 5.5))
        self.assertEqual(self.db.get_lot("4001")["price_per_hour"], 5.5)
        self.assertEqual(fields.fields["price"], "5.5")
        self.assertEqual(fake_account.save_lot.await_count, 1)
        self.assertEqual(sync.await_count, 2)

    async def test_listing_preview_requires_mmr_and_renders_safe_fields(self):
        account = {
            "mmr": 5000,
            "behavior_score": None,
        }
        title, description = build_listing_text(account, 2.5, language="ru")
        self.assertTrue(title)
        self.assertTrue(description)
        self.assertIn("2.5", description)
        with self.assertRaises(ValueError):
            build_listing_text({"mmr": None, "behavior_score": None}, 2.5)

    async def test_main_wires_workers_and_closes_database(self):
        db = SimpleNamespace(close=Mock())
        bot = SimpleNamespace(
            start=AsyncMock(),
            sync_account_listing=AsyncMock(),
        )
        with (
            patch.object(app_main, "Database", return_value=db),
            patch.object(app_main, "RentalBot", return_value=bot),
            patch.object(app_main, "daily_checks", new_callable=AsyncMock) as checks,
            patch.object(
                app_main, "password_worker", new_callable=AsyncMock
            ) as passwords,
            patch.object(app_main, "digest_loop", new_callable=AsyncMock) as digest,
            patch.object(
                app_main, "critical_notification_loop", new_callable=AsyncMock
            ) as critical,
            patch.object(app_main, "admin_menu_loop", new_callable=AsyncMock) as menu,
        ):
            await app_main.main()
        bot.start.assert_awaited_once()
        db.close.assert_called_once()
        checks.assert_called_once_with(db, bot.sync_account_listing)
        passwords.assert_called_once_with(db)
        digest.assert_called_once_with(db)
        critical.assert_called_once_with(db)
        menu.assert_called_once_with(db, bot)


if __name__ == "__main__":
    unittest.main()
