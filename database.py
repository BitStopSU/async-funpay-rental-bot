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
            login TEXT UNIQUE NOT NULL,
            password_enc BLOB NOT NULL,
            shared_secret_enc BLOB NOT NULL,
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
        CREATE INDEX IF NOT EXISTS idx_rentals_expiry ON rentals(status, ends_at);
        CREATE INDEX IF NOT EXISTS idx_accounts_free ON accounts(status, mmr DESC);
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
        if "account_id" not in lot_columns:
            self.conn.execute(
                "ALTER TABLE lots ADD COLUMN account_id INTEGER REFERENCES accounts(account_id)"
            )
        self.conn.commit()

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
        login: str,
        password: str,
        shared_secret: str,
        steamid64: str | None = None,
        dota_account_id: str | None = None,
        mmr: int | None = None,
    ) -> int:
        if not login.strip() or not password or not shared_secret:
            raise ValueError("Login, password, and shared secret are required")
        with self.conn:
            cur = self.conn.execute(
                """INSERT INTO accounts
                   (login, password_enc, shared_secret_enc, steamid64,
                    dota_account_id, mmr, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    login.strip(), self.encrypt(password), self.encrypt(shared_secret),
                    steamid64.strip() if steamid64 and steamid64.strip() else None,
                    (
                        dota_account_id.strip()
                        if dota_account_id and dota_account_id.strip()
                        else None
                    ),
                    mmr,
                    current_time().isoformat(),
                ),
            )
            account_id = cur.lastrowid
            self.log("account_added", account_id=account_id)
            return account_id

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
        return self.conn.execute(
            "SELECT * FROM lots WHERE title = ? COLLATE NOCASE",
            (title.strip(),),
        ).fetchone()

    def register_lot(
        self,
        lot_id: str,
        title: str,
        price_per_hour: float,
        account_id: int,
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
            duplicate_title = self.conn.execute(
                "SELECT 1 FROM lots WHERE title = ? COLLATE NOCASE",
                (title.strip(),),
            ).fetchone()
            if duplicate_title:
                raise ValueError("Listing title must be unique for order matching")
            already_linked = self.conn.execute(
                "SELECT lot_id FROM lots WHERE account_id = ?",
                (account_id,),
            ).fetchone()
            if already_linked:
                raise ValueError("This account already has a registered lot")
            self.conn.execute(
                """INSERT INTO lots (lot_id, title, price_per_hour, is_extension, account_id)
                   VALUES (?, ?, ?, 0, ?)""",
                (str(lot_id).strip(), title.strip(), float(price_per_hour), account_id),
            )
            self.log(
                "account_lot_registered",
                account_id=account_id,
                details={"lot_id": str(lot_id).strip()},
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
            self.conn.execute(
                "UPDATE accounts SET mmr = ?, last_check = ? WHERE account_id = ?",
                (mmr, current_time().isoformat(), account_id),
            )
            self.log(
                "account_mmr_checked", account_id=account_id,
                details={"mmr": mmr},
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
