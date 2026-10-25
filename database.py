import json
import math
import sqlite3
from datetime import datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet

from config import Config
from i18n import tr


def current_time() -> datetime:
    return datetime.now()


class Database:
    def __init__(self, path: str | None = None):
        if not Config.SECRET_KEY:
            raise ValueError(tr("secret_key_missing"))
        self.cipher = Fernet(Config.SECRET_KEY.encode())
        self.conn = sqlite3.connect(
            path or Config.DB_PATH, check_same_thread=False, timeout=30
        )
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA busy_timeout=30000")
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            funpay_nick TEXT UNIQUE NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT,
            total_orders INTEGER DEFAULT 0,
            total_hours INTEGER DEFAULT 0,
            trust_level TEXT DEFAULT 'new',
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS accounts (
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
        CREATE TABLE IF NOT EXISTS lots (
            lot_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            title_en TEXT,
            price_per_hour REAL NOT NULL,
            is_extension INTEGER DEFAULT 0,
            account_id INTEGER REFERENCES accounts(account_id)
        );
        CREATE TABLE IF NOT EXISTS rentals (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id),
            account_id INTEGER NOT NULL REFERENCES accounts(account_id),
            lot_id TEXT NOT NULL REFERENCES lots(lot_id),
            quantity INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            ends_at TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            buyer_nick TEXT NOT NULL,
            chat_id TEXT
        );
        CREATE TABLE IF NOT EXISTS logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            event_type TEXT NOT NULL,
            user_id INTEGER,
            account_id INTEGER,
            order_id TEXT,
            details TEXT,
            severity TEXT DEFAULT 'info'
        );
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            text TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'warning',
            sent INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS password_tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL REFERENCES accounts(account_id),
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            completed_at TEXT,
            note TEXT
        );
        CREATE TABLE IF NOT EXISTS processed_orders (
            order_id TEXT PRIMARY KEY,
            rental_order_id TEXT,
            order_type TEXT NOT NULL,
            processed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS screenshot_submissions (
            submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL REFERENCES rentals(order_id),
            account_id INTEGER NOT NULL REFERENCES accounts(account_id),
            buyer_nick TEXT NOT NULL,
            source_chat_id TEXT NOT NULL,
            source_message_id TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'sending',
            telegram_message_id INTEGER,
            telegram_file_id TEXT,
            UNIQUE (source_chat_id, source_message_id)
        );
        CREATE INDEX IF NOT EXISTS idx_rentals_expiry ON rentals(status, ends_at);
        CREATE INDEX IF NOT EXISTS idx_notifications_pending
            ON notifications(sent, severity);
        CREATE INDEX IF NOT EXISTS idx_password_tasks_pending
            ON password_tasks(status, task_id);
        """)
        # Upgrade databases created before chat binding and notification support.
        rental_columns = {
            row["name"] for row in self.conn.execute("PRAGMA table_info(rentals)")
        }
        if "chat_id" not in rental_columns:
            self.conn.execute("ALTER TABLE rentals ADD COLUMN chat_id TEXT")
        lot_columns = {
            row["name"] for row in self.conn.execute("PRAGMA table_info(lots)")
        }
        if "title_en" not in lot_columns:
            self.conn.execute("ALTER TABLE lots ADD COLUMN title_en TEXT")
        if "account_id" not in lot_columns:
            self.conn.execute(
                "ALTER TABLE lots ADD COLUMN account_id INTEGER REFERENCES accounts(account_id)"
            )
        self._migrate_optional_account_credentials()
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_accounts_free ON accounts(status, mmr DESC)"
        )
        self.conn.commit()

    def _migrate_optional_account_credentials(self):
        columns = {
            row["name"]: row for row in self.conn.execute("PRAGMA table_info(accounts)")
        }
        required_columns = {"login", "password_enc", "shared_secret_enc"}
        if not required_columns.issubset(columns) or not any(
            columns[name]["notnull"] for name in required_columns
        ):
            return

        self.conn.execute("PRAGMA foreign_keys=OFF")
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            self.conn.execute("""
                CREATE TABLE accounts_new (
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
                )
            """)
            self.conn.execute("""
                INSERT INTO accounts_new
                SELECT account_id, login, password_enc, shared_secret_enc,
                       email_login, email_password_enc, steamid64,
                       dota_account_id, mmr, behavior_score, vac_banned, status,
                       auto_change_password, last_check, created_at
                FROM accounts
            """)
            self.conn.execute("DROP TABLE accounts")
            self.conn.execute("ALTER TABLE accounts_new RENAME TO accounts")
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            self.conn.execute("PRAGMA foreign_keys=ON")

    def close(self):
        self.conn.close()

    def encrypt(self, value: str) -> bytes:
        return self.cipher.encrypt(value.encode())

    def decrypt(self, value: bytes) -> str:
        return self.cipher.decrypt(value).decode()

    def get_or_create_user(self, nick: str) -> int:
        now = current_time().isoformat()
        with self.conn:
            row = self.conn.execute(
                "SELECT user_id FROM users WHERE funpay_nick = ?", (nick,)
            ).fetchone()
            if row:
                self.conn.execute(
                    "UPDATE users SET last_seen = ? WHERE user_id = ?",
                    (now, row["user_id"]),
                )
                return row["user_id"]
            cur = self.conn.execute(
                "INSERT INTO users (funpay_nick, first_seen, last_seen) VALUES (?, ?, ?)",
                (nick, now, now),
            )
            return cur.lastrowid

    def get_free_account(self, min_mmr: int = 0):
        return self.conn.execute(
            """SELECT * FROM accounts
               WHERE status = 'free' AND vac_banned = 0 AND mmr >= ?
                 AND NOT EXISTS (
                     SELECT 1 FROM rentals
                     WHERE rentals.account_id = accounts.account_id
                       AND rentals.status = 'active'
                 )
               ORDER BY mmr DESC LIMIT 1""",
            (min_mmr,),
        ).fetchone()

    def get_free_account_for_lot(self, lot_id: str, min_mmr: int = 0):
        lot = self.get_lot(lot_id)
        if not lot:
            return None
        if lot["account_id"] is None:
            return self.get_free_account(min_mmr)
        return self.conn.execute(
            """SELECT * FROM accounts
               WHERE account_id = ? AND status = 'free' AND vac_banned = 0
                 AND mmr >= ?
                 AND NOT EXISTS (
                     SELECT 1 FROM rentals
                     WHERE rentals.account_id = accounts.account_id
                       AND rentals.status = 'active'
                 )""",
            (lot["account_id"], min_mmr),
        ).fetchone()

    def add_account(
        self,
        login: str | None = None,
        password: str | None = None,
        shared_secret: str | None = None,
        steamid64: str | None = None,
        dota_account_id: str | None = None,
        mmr: int | None = None,
        behavior_score: int | None = None,
    ) -> int:
        supplied_credentials = any((login, password, shared_secret))
        if supplied_credentials and not all(
            (login and login.strip(), password, shared_secret)
        ):
            raise ValueError("Provide all credentials together or omit them all")
        if not supplied_credentials and not (steamid64 or dota_account_id):
            raise ValueError("A SteamID64 or Dota account ID is required")
        if steamid64 and (not steamid64.isdecimal() or len(steamid64) != 17):
            raise ValueError("SteamID64 must contain 17 digits")
        if dota_account_id and not dota_account_id.isdecimal():
            raise ValueError("Dota account ID must contain digits only")
        if mmr is not None and not 0 <= mmr <= 15000:
            raise ValueError("MMR must be between 0 and 15000")
        if behavior_score is not None and not 0 <= behavior_score <= 12000:
            raise ValueError("Behavior score must be between 0 and 12000")
        with self.conn:
            cur = self.conn.execute(
                """INSERT INTO accounts
                   (login, password_enc, shared_secret_enc, steamid64,
                    dota_account_id, mmr, behavior_score, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    login.strip() if login else None,
                    self.encrypt(password) if password else None,
                    self.encrypt(shared_secret) if shared_secret else None,
                    steamid64.strip() if steamid64 and steamid64.strip() else None,
                    (
                        dota_account_id.strip()
                        if dota_account_id and dota_account_id.strip()
                        else None
                    ),
                    mmr,
                    behavior_score,
                    current_time().isoformat(),
                ),
            )
            account_id = cur.lastrowid
            self.log("account_added", account_id=account_id)
            return account_id

    def get_account_listing_data(self, account_id: int):
        return self.conn.execute(
            """SELECT account_id, steamid64, dota_account_id, mmr,
                      behavior_score, status, vac_banned
               FROM accounts WHERE account_id = ?""",
            (account_id,),
        ).fetchone()

    def get_admin_editable_accounts(self):
        return self.conn.execute(
            """SELECT account_id, steamid64, dota_account_id, mmr,
                      behavior_score, status, vac_banned
               FROM accounts ORDER BY account_id"""
        ).fetchall()

    def update_account_public_field(
        self, account_id: int, field: str, value: str | int
    ):
        columns = {
            "steamid64": "steamid64",
            "dota_account_id": "dota_account_id",
            "mmr": "mmr",
            "behavior_score": "behavior_score",
        }
        if field not in columns:
            raise ValueError("Unsupported account field")
        if field in {"steamid64", "dota_account_id"}:
            normalized = str(value).strip()
            if not normalized.isdecimal():
                raise ValueError("Account IDs must contain digits only")
            if field == "steamid64" and len(normalized) != 17:
                raise ValueError("SteamID64 must contain 17 digits")
        else:
            if isinstance(value, bool) or not str(value).isdecimal():
                raise ValueError("Value must be a non-negative integer")
            normalized = int(value)
            max_value = 12000 if field == "behavior_score" else 15000
            if normalized > max_value:
                raise ValueError(f"{field} exceeds its supported range")
        with self.conn:
            cursor = self.conn.execute(
                f"UPDATE accounts SET {columns[field]} = ? WHERE account_id = ?",
                (normalized, account_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Account does not exist")
            self.log(
                f"account_{field}_updated",
                account_id=account_id,
                details={"value": normalized},
            )
        return normalized

    def start_screenshot_submission(
        self,
        order_id: str,
        account_id: int,
        buyer_nick: str,
        source_chat_id: str,
        source_message_id: str,
    ) -> int | None:
        with self.conn:
            cur = self.conn.execute(
                """INSERT OR IGNORE INTO screenshot_submissions
                   (order_id, account_id, buyer_nick, source_chat_id,
                    source_message_id, submitted_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'sending')""",
                (
                    str(order_id),
                    account_id,
                    buyer_nick,
                    str(source_chat_id),
                    str(source_message_id),
                    current_time().isoformat(),
                ),
            )
            if cur.rowcount == 0:
                return None
            submission_id = cur.lastrowid
            self.log(
                "profile_screenshot_received",
                account_id=account_id,
                order_id=str(order_id),
                details={
                    "submission_id": submission_id,
                    "source_message_id": str(source_message_id),
                },
            )
            return submission_id

    def mark_screenshot_submission_sent(
        self,
        submission_id: int,
        telegram_message_id: int,
        telegram_file_id: str | None,
    ):
        with self.conn:
            row = self.conn.execute(
                """SELECT order_id, account_id FROM screenshot_submissions
                   WHERE submission_id = ? AND status = 'sending'""",
                (submission_id,),
            ).fetchone()
            if not row:
                return False
            self.conn.execute(
                """UPDATE screenshot_submissions
                   SET status = 'sent', telegram_message_id = ?,
                       telegram_file_id = ?
                   WHERE submission_id = ? AND status = 'sending'""",
                (telegram_message_id, telegram_file_id, submission_id),
            )
            self.log(
                "profile_screenshot_stored_in_telegram",
                account_id=row["account_id"],
                order_id=row["order_id"],
                details={
                    "submission_id": submission_id,
                    "telegram_message_id": telegram_message_id,
                },
            )
            return True

    def mark_screenshot_submission_failed(self, submission_id: int):
        with self.conn:
            row = self.conn.execute(
                """SELECT order_id, account_id FROM screenshot_submissions
                   WHERE submission_id = ? AND status = 'sending'""",
                (submission_id,),
            ).fetchone()
            if not row:
                return False
            self.conn.execute(
                """UPDATE screenshot_submissions SET status = 'failed'
                   WHERE submission_id = ? AND status = 'sending'""",
                (submission_id,),
            )
            self.log(
                "profile_screenshot_telegram_delivery_failed",
                account_id=row["account_id"],
                order_id=row["order_id"],
                details={"submission_id": submission_id},
                severity="error",
            )
            return True

    def set_account_status(self, account_id: int, status: str):
        if status not in {"free", "rented", "banned", "maintenance"}:
            raise ValueError(f"Invalid account status: {status}")
        with self.conn:
            self.conn.execute(
                """UPDATE accounts
                   SET status = CASE
                       WHEN vac_banned = 1 THEN 'banned'
                       WHEN EXISTS (
                           SELECT 1 FROM rentals
                           WHERE rentals.account_id = accounts.account_id
                             AND rentals.status = 'active'
                       ) THEN 'rented'
                       ELSE ? END
                   WHERE account_id = ?""",
                (status, account_id),
            )

    def get_active_rental_by_buyer(self, nick: str):
        return self.conn.execute(
            """SELECT * FROM rentals
               WHERE buyer_nick = ? COLLATE NOCASE AND status = 'active'""",
            (nick,),
        ).fetchone()

    def is_order_processed(self, order_id: str) -> bool:
        return self.conn.execute(
            "SELECT 1 FROM processed_orders WHERE order_id = ?",
            (str(order_id),),
        ).fetchone() is not None

    def get_active_rental_by_chat(self, chat_id: str):
        return self.conn.execute(
            """SELECT * FROM rentals WHERE chat_id = ? AND status = 'active'
               ORDER BY started_at DESC LIMIT 1""",
            (str(chat_id),),
        ).fetchone()

    def get_lot(self, lot_id: str):
        return self.conn.execute(
            "SELECT * FROM lots WHERE lot_id = ?", (str(lot_id),)
        ).fetchone()

    def get_lot_by_title(self, title: str):
        rows = self.conn.execute(
            """SELECT * FROM lots
               WHERE title = ? COLLATE NOCASE
                  OR title_en = ? COLLATE NOCASE
               LIMIT 2""",
            (title.strip(), title.strip()),
        ).fetchall()
        return rows[0] if len(rows) == 1 else None

    def register_lot(
        self,
        lot_id: str,
        title: str,
        price_per_hour: float,
        account_id: int,
        title_en: str | None = None,
    ):
        if not str(lot_id).strip() or not title.strip():
            raise ValueError("Lot ID and title are required")
        if float(price_per_hour) <= 0:
            raise ValueError("Hourly price must be positive")
        if not math.isfinite(float(price_per_hour)):
            raise ValueError("Hourly price must be finite")
        with self.conn:
            account = self.conn.execute(
                "SELECT account_id FROM accounts WHERE account_id = ?",
                (account_id,),
            ).fetchone()
            if not account:
                raise ValueError("Account does not exist")
            existing = self.conn.execute(
                "SELECT account_id FROM lots WHERE lot_id = ?",
                (str(lot_id).strip(),),
            ).fetchone()
            if existing:
                raise ValueError("This FunPay lot is already registered")
            already_linked = self.conn.execute(
                "SELECT lot_id FROM lots WHERE account_id = ?",
                (account_id,),
            ).fetchone()
            if already_linked:
                raise ValueError("This account already has a registered lot")
            self.conn.execute(
                """INSERT INTO lots
                   (lot_id, title, title_en, price_per_hour, is_extension, account_id)
                   VALUES (?, ?, ?, ?, 0, ?)""",
                (
                    str(lot_id).strip(),
                    title.strip(),
                    title_en.strip() if title_en and title_en.strip() else None,
                    float(price_per_hour),
                    account_id,
                ),
            )
            self.log(
                "account_lot_registered",
                account_id=account_id,
                details={"lot_id": str(lot_id).strip()},
            )

    def get_unlinked_accounts(self):
        return self.conn.execute(
            """SELECT account_id, dota_account_id, mmr, behavior_score
               FROM accounts
               WHERE status = 'free' AND vac_banned = 0
                 AND account_id NOT IN (
                     SELECT account_id FROM lots WHERE account_id IS NOT NULL
                 )
               ORDER BY account_id"""
        ).fetchall()

    def set_dota_account_id(self, account_id: int, dota_account_id: str):
        value = str(dota_account_id).strip()
        if not value.isdecimal():
            raise ValueError("Dota account ID must be numeric")
        with self.conn:
            cursor = self.conn.execute(
                "UPDATE accounts SET dota_account_id = ? WHERE account_id = ?",
                (value, account_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Account does not exist")
            self.log(
                "account_dota_id_updated",
                account_id=account_id,
            )

    def get_lot_by_account_id(self, account_id: int):
        return self.conn.execute(
            "SELECT * FROM lots WHERE account_id = ? AND is_extension = 0",
            (account_id,),
        ).fetchone()

    def get_lots_for_sync(self):
        return self.conn.execute(
            """SELECT lots.lot_id, lots.price_per_hour, lots.title, lots.title_en,
                      accounts.account_id, accounts.mmr, accounts.behavior_score
               FROM lots JOIN accounts ON accounts.account_id = lots.account_id
               WHERE lots.is_extension = 0 AND accounts.vac_banned = 0
               ORDER BY lots.lot_id"""
        ).fetchall()

    def update_lot_titles(
        self, lot_id: str, title: str, title_en: str
    ):
        with self.conn:
            self.conn.execute(
                "UPDATE lots SET title = ?, title_en = ? WHERE lot_id = ?",
                (title, title_en, str(lot_id)),
            )
            self.log(
                "listing_titles_synchronized",
                details={"lot_id": str(lot_id)},
            )

    def update_lot_price(self, lot_id: str, price_per_hour: float):
        price = float(price_per_hour)
        if not math.isfinite(price) or price <= 0:
            raise ValueError("Hourly price must be a positive finite number")
        with self.conn:
            cursor = self.conn.execute(
                "UPDATE lots SET price_per_hour = ? WHERE lot_id = ?",
                (price, str(lot_id)),
            )
            if cursor.rowcount != 1:
                raise ValueError("Lot does not exist")
            row = self.conn.execute(
                "SELECT account_id FROM lots WHERE lot_id = ?",
                (str(lot_id),),
            ).fetchone()
            self.log(
                "listing_price_updated",
                account_id=row["account_id"],
                details={"lot_id": str(lot_id), "price_per_hour": price},
            )

    def get_admin_status(self) -> dict[str, int]:
        account_rows = self.conn.execute(
            "SELECT status, COUNT(*) AS count FROM accounts GROUP BY status"
        ).fetchall()
        status = {row["status"]: row["count"] for row in account_rows}
        return {
            "accounts_total": sum(status.values()),
            "accounts_free": status.get("free", 0),
            "accounts_rented": status.get("rented", 0),
            "accounts_maintenance": status.get("maintenance", 0),
            "accounts_banned": status.get("banned", 0),
            "vac_banned": self.conn.execute(
                "SELECT COUNT(*) FROM accounts WHERE vac_banned = 1"
            ).fetchone()[0],
            "active_rentals": self.conn.execute(
                "SELECT COUNT(*) FROM rentals WHERE status = 'active'"
            ).fetchone()[0],
            "expired_unreleased": self.conn.execute(
                """SELECT COUNT(*) FROM rentals
                   WHERE status = 'active' AND ends_at <= ?""",
                (current_time().isoformat(),),
            ).fetchone()[0],
            "lots_total": self.conn.execute(
                "SELECT COUNT(*) FROM lots"
            ).fetchone()[0],
            "unlinked_accounts": self.conn.execute(
                """SELECT COUNT(*) FROM accounts
                   WHERE NOT EXISTS (
                       SELECT 1 FROM lots WHERE lots.account_id = accounts.account_id
                   )"""
            ).fetchone()[0],
            "manual_tasks": self.conn.execute(
                "SELECT COUNT(*) FROM password_tasks WHERE status IN ('pending', 'notified')"
            ).fetchone()[0],
        }

    def get_admin_accounts(self):
        return self.conn.execute(
            """SELECT accounts.account_id, accounts.status, accounts.mmr,
                      accounts.vac_banned, lots.lot_id
               FROM accounts LEFT JOIN lots USING (account_id)
               ORDER BY accounts.account_id"""
        ).fetchall()

    def get_admin_lots(self):
        return self.conn.execute(
            """SELECT lot_id, title, price_per_hour, is_extension, account_id
               FROM lots ORDER BY lot_id"""
        ).fetchall()

    def get_admin_active_rentals(self):
        return self.conn.execute(
            """SELECT order_id, buyer_nick, account_id, ends_at, lot_id
               FROM rentals WHERE status = 'active'
               ORDER BY ends_at"""
        ).fetchall()

    def create_rental(
        self, order_id, user_id, account_id, lot_id, quantity, buyer_nick,
        chat_id=None,
    ):
        if int(quantity) <= 0:
            raise ValueError("Rental quantity must be positive")
        now = current_time()
        ends = now + timedelta(hours=int(quantity), minutes=Config.BUFFER_MINUTES)
        with self.conn:
            if self.conn.execute(
                "SELECT 1 FROM rentals WHERE order_id = ?", (str(order_id),)
            ).fetchone():
                raise ValueError("Order has already been processed")
            if self.get_active_rental_by_buyer(buyer_nick):
                raise ValueError("Buyer already has an active rental")
            account = self.conn.execute(
                """SELECT accounts.status, accounts.vac_banned,
                          EXISTS (SELECT 1 FROM rentals
                                  WHERE rentals.account_id = accounts.account_id
                                    AND rentals.status = 'active') AS has_active_rental
                   FROM accounts WHERE account_id = ?""",
                (account_id,),
            ).fetchone()
            if (
                not account or account["status"] != "free"
                or account["vac_banned"] or account["has_active_rental"]
            ):
                raise ValueError("Account is not available")
            lot = self.get_lot(str(lot_id))
            if not lot or (
                lot["account_id"] is not None
                and lot["account_id"] != int(account_id)
            ):
                raise ValueError("Account is not assigned to this lot")
            self.conn.execute(
                """INSERT INTO rentals
                   (order_id, user_id, account_id, lot_id, quantity, started_at,
                    ends_at, buyer_nick, chat_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(order_id), user_id, account_id, str(lot_id), int(quantity),
                    now.isoformat(), ends.isoformat(), buyer_nick,
                    str(chat_id) if chat_id is not None else None,
                ),
            )
            self.conn.execute(
                "UPDATE accounts SET status = 'rented' WHERE account_id = ?",
                (account_id,),
            )
            self.conn.execute(
                """INSERT INTO processed_orders
                   (order_id, rental_order_id, order_type, processed_at)
                   VALUES (?, ?, 'rental', ?)""",
                (str(order_id), str(order_id), now.isoformat()),
            )
            self.conn.execute(
                """UPDATE users SET total_orders = total_orders + 1,
                   total_hours = total_hours + ? WHERE user_id = ?""",
                (int(quantity), user_id),
            )
            self.log(
                "rental_created", user_id=user_id, account_id=account_id,
                order_id=str(order_id),
                details={"hours": int(quantity), "ends": ends.isoformat()},
            )
        return ends

    def extend_rental(
        self, order_id: str, extra_hours: int, extension_order_id: str | None = None
    ):
        if int(extra_hours) <= 0:
            raise ValueError("Extension quantity must be positive")
        with self.conn:
            rental = self.conn.execute(
                """SELECT rentals.*, accounts.auto_change_password
                   FROM rentals JOIN accounts USING (account_id)
                   WHERE rentals.order_id = ? AND rentals.status = 'active'""",
                (str(order_id),),
            ).fetchone()
            if not rental:
                return None
            if extension_order_id and self.conn.execute(
                "SELECT 1 FROM processed_orders WHERE order_id = ?",
                (str(extension_order_id),),
            ).fetchone():
                return datetime.fromisoformat(rental["ends_at"])
            new_ends = datetime.fromisoformat(rental["ends_at"]) + timedelta(
                hours=int(extra_hours)
            )
            self.conn.execute(
                """UPDATE rentals SET ends_at = ?, quantity = quantity + ?
                   WHERE order_id = ? AND status = 'active'""",
                (new_ends.isoformat(), int(extra_hours), str(order_id)),
            )
            if extension_order_id:
                self.conn.execute(
                    """INSERT INTO processed_orders
                       (order_id, rental_order_id, order_type, processed_at)
                       VALUES (?, ?, 'extension', ?)""",
                    (
                        str(extension_order_id), str(order_id), current_time().isoformat(),
                    ),
                )
            self.conn.execute(
                """UPDATE users SET total_orders = total_orders + 1,
                   total_hours = total_hours + ? WHERE user_id = ?""",
                (int(extra_hours), rental["user_id"]),
            )
            self.log(
                "rental_extended", user_id=rental["user_id"],
                account_id=rental["account_id"],
                order_id=str(extension_order_id or order_id),
                details={
                    "rental_order_id": str(order_id),
                    "added_hours": int(extra_hours),
                    "new_ends": new_ends.isoformat(),
                },
            )
            return new_ends

    def get_expired_rentals(self):
        return self.conn.execute(
            "SELECT * FROM rentals WHERE status = 'active' AND ends_at <= ?",
            (current_time().isoformat(),),
        ).fetchall()

    def release_expired_rental(self, order_id: str):
        """Atomically re-check expiry, end the rental, then release its account."""
        now = current_time()
        with self.conn:
            rental = self.conn.execute(
                """SELECT rentals.*, accounts.auto_change_password
                   FROM rentals JOIN accounts USING (account_id)
                   WHERE rentals.order_id = ? AND rentals.status = 'active'""",
                (str(order_id),),
            ).fetchone()
            if not rental or datetime.fromisoformat(rental["ends_at"]) > now:
                return None
            self.conn.execute(
                "UPDATE rentals SET status = 'expired' WHERE order_id = ?",
                (str(order_id),),
            )
            self.conn.execute(
                """UPDATE accounts
                   SET status = CASE
                       WHEN vac_banned = 1 THEN 'banned'
                       WHEN EXISTS (
                           SELECT 1 FROM rentals
                           WHERE rentals.account_id = accounts.account_id
                             AND rentals.status = 'active'
                       ) THEN 'rented'
                       ELSE 'free' END
                   WHERE account_id = ?""",
                (rental["account_id"],),
            )
            self.log(
                "rental_expired", account_id=rental["account_id"],
                order_id=str(order_id),
            )
            if rental["auto_change_password"]:
                cur = self.conn.execute(
                    """INSERT INTO password_tasks (account_id, created_at, note)
                       VALUES (?, ?, ?)""",
                    (
                        rental["account_id"], now.isoformat(),
                        f"Rental {order_id} ended; manual review only",
                    ),
                )
                self.log(
                    "password_task_queued", account_id=rental["account_id"],
                    order_id=str(order_id), details={"task_id": cur.lastrowid},
                )
            return rental

    def mark_vac_banned(self, steamid64: str):
        with self.conn:
            rows = self.conn.execute(
                "SELECT account_id FROM accounts WHERE steamid64 = ? AND vac_banned = 0",
                (str(steamid64),),
            ).fetchall()
            self.conn.execute(
                """UPDATE accounts SET vac_banned = 1, status = 'banned'
                   WHERE steamid64 = ?""",
                (str(steamid64),),
            )
            for row in rows:
                self.log(
                    "account_vac_detected", account_id=row["account_id"],
                    details={"steamid": str(steamid64)}, severity="critical",
                )
        return len(rows)

    def update_mmr(self, account_id: int, mmr: int | None):
        with self.conn:
            row = self.conn.execute(
                "SELECT mmr FROM accounts WHERE account_id = ?",
                (account_id,),
            ).fetchone()
            if not row:
                raise ValueError("Account does not exist")
            changed = row["mmr"] != mmr
            self.conn.execute(
                "UPDATE accounts SET mmr = ?, last_check = ? WHERE account_id = ?",
                (mmr, current_time().isoformat(), account_id),
            )
            self.log(
                "account_mmr_checked", account_id=account_id,
                details={"mmr": mmr},
            )
            return changed

    def update_behavior_score(self, account_id: int, behavior_score: int):
        if behavior_score < 0:
            raise ValueError("Behavior score must be non-negative")
        with self.conn:
            cursor = self.conn.execute(
                "UPDATE accounts SET behavior_score = ? WHERE account_id = ?",
                (behavior_score, account_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Account does not exist")
            self.log(
                "account_behavior_score_updated",
                account_id=account_id,
                details={"behavior_score": behavior_score},
            )

    def queue_password_task(self, account_id: int, note: str = "") -> int:
        with self.conn:
            cur = self.conn.execute(
                """INSERT INTO password_tasks (account_id, created_at, note)
                   VALUES (?, ?, ?)""",
                (account_id, current_time().isoformat(), note),
            )
            task_id = cur.lastrowid
            self.log(
                "password_task_queued", account_id=account_id,
                details={"task_id": task_id},
            )
            return task_id

    def get_next_password_task(self):
        return self.conn.execute(
            """SELECT * FROM password_tasks WHERE status = 'pending'
               ORDER BY task_id LIMIT 1"""
        ).fetchone()

    def mark_password_task_notified(self, task_id: int, account_id: int):
        with self.conn:
            self.conn.execute(
                """UPDATE password_tasks SET status = 'notified'
                   WHERE task_id = ? AND status = 'pending'""",
                (task_id,),
            )
            self.log(
                "password_task_admin_notified", account_id=account_id,
                details={"task_id": task_id},
            )

    def queue_notification(self, text: str, severity: str = "warning"):
        with self.conn:
            self.conn.execute(
                "INSERT INTO notifications (ts, text, severity) VALUES (?, ?, ?)",
                (current_time().isoformat(), text[:4000], severity),
            )

    def get_pending_notifications(
        self, limit: int = 20, severity: str | None = None
    ):
        if severity is None:
            return self.conn.execute(
                """SELECT notification_id, text, severity FROM notifications
                   WHERE sent = 0
                   ORDER BY notification_id LIMIT ?""",
                (limit,),
            ).fetchall()
        return self.conn.execute(
            """SELECT notification_id, text, severity FROM notifications
               WHERE sent = 0 AND severity = ?
               ORDER BY notification_id LIMIT ?""",
            (severity, limit),
        ).fetchall()

    def mark_notifications_sent(self, ids: list[int]):
        if not ids:
            return
        with self.conn:
            self.conn.executemany(
                "UPDATE notifications SET sent = 1 WHERE notification_id = ?",
                [(item_id,) for item_id in ids],
            )

    def log(
        self, event_type: str, user_id: int | None = None,
        account_id: int | None = None, order_id: str | None = None,
        details: dict[str, Any] | None = None, severity: str = "info",
    ):
        self.conn.execute(
            """INSERT INTO logs
               (ts, event_type, user_id, account_id, order_id, details, severity)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                current_time().isoformat(), event_type, user_id, account_id, order_id,
                json.dumps(details, ensure_ascii=False) if details else None,
                severity,
            ),
        )
