from config import Config

_MESSAGES = {
    "ru": {
        "order_already_registered": "Этот заказ уже зарегистрирован.",
        "paid_order_operator": "Оплата получена. Заказ передан оператору.",
        "extension_operator": "Оплата получена. Для этого заказа требуется оператор.",
        "extension_confirmed": "Аренда продлена на {hours} ч. Доступ до: {ends}.",
        "already_renting": (
            "Оплата получена. У вас уже есть активный заказ; обратитесь к оператору."
        ),
        "no_accounts": (
            "Оплата получена. Сейчас нет доступного аккаунта; обратитесь к оператору."
        ),
        "manual_fulfillment": (
            "Оплата получена, заказ зарегистрирован. Для дальнейших действий "
            "обратитесь к оператору."
        ),
        "credential_request_active": (
            "Автоматическая выдача кодов и данных аккаунта отключена. "
            "Обратитесь к оператору."
        ),
        "credential_request_inactive": "Активная аренда для этого чата не найдена.",
        "notify_lot_unmatched": (
            "Не удалось сопоставить оплаченный заказ №{order_id} "
            "с настроенным лотом."
        ),
        "notify_extension_unmatched": (
            "Для оплаченного продления №{order_id} не найдена активная аренда."
        ),
        "notify_buyer_already_renting": (
            "Оплаченный заказ №{order_id}: у покупателя уже есть активная аренда."
        ),
        "notify_no_accounts": (
            "Оплаченный заказ №{order_id}: в пуле нет свободных аккаунтов."
        ),
        "notify_order_failed": (
            "Не удалось зарегистрировать оплаченный заказ №{order_id}; "
            "требуется вмешательство оператора."
        ),
        "notify_manual_fulfillment": (
            "Заказ №{order_id} зарегистрирован для аккаунта №{account_id}; "
            "автоматическая выдача данных отключена."
        ),
        "notify_password_manual": (
            "Аренда завершена: для аккаунта №{account_id} "
            "требуется ручная проверка пароля."
        ),
        "notify_vac_disabled": (
            "Проверка VAC в Steam пропущена: не задан STEAM_API_KEY."
        ),
        "notify_vac_banned": (
            "Аккаунты со VAC-баном исключены из пула. SteamID: {steam_id}."
        ),
        "notify_vac_failed": (
            "Не удалось проверить VAC-бан в Steam. Подробности — в журнале приложения."
        ),
        "notify_mmr_failed": (
            "Не удалось проверить MMR в OpenDota для аккаунта №{account_id}."
        ),
        "digest_warning_title": "⚠️ Дайджест предупреждений:",
        "digest_critical_title": "🚨 Дайджест уведомлений:",
        "severity_warning": "предупреждение",
        "severity_critical": "критически важно",
        "telegram_credentials_missing": (
            "Для отправки уведомлений Telegram необходимо задать "
            "TG_BOT_TOKEN и TG_ADMIN_ID"
        ),
        "funpay_key_missing": "Необходимо задать FUNPAY_GOLDEN_KEY",
        "secret_key_missing": "В SECRET_KEY необходимо указать ключ Fernet",
        "telegram_rejected": "Telegram отклонил уведомление",
        "telegram_digest_failed": "Не удалось отправить дайджест уведомлений (%s)",
        "telegram_critical_failed": (
            "Не удалось немедленно отправить критическое уведомление (%s)"
        ),
        "telegram_password_task": (
            "Для аккаунта №{account_id} требуется ручная проверка пароля "
            "(задача №{task_id}). Автоматический доступ к паролю или почте "
            "не выполнялся."
        ),
        "telegram_password_task_failed": (
            "Не удалось уведомить администратора о задаче проверки пароля (%s)"
        ),
        "ticker_failed": "Ошибка проверки истёкших аренд (%s)",
        "funpay_started": "Обработчик событий FunPay запущен",
        "funpay_handler_failed": "Ошибка обработки события FunPay (%s)",
        "funpay_cookie_refresh": "Сессия FunPay отклонена; обновляю данные сессии",
        "daily_vac_failed": "Не удалось проверить VAC-бан в Steam (%s)",
        "daily_mmr_failed": (
            "Не удалось проверить MMR в OpenDota для аккаунта №%s (%s)"
        ),
        "daily_checks_failed": (
            "Не удалось выполнить ежедневные проверки аккаунтов (%s)"
        ),
        "steam_response_invalid": "В ответе Steam отсутствует список игроков",
        "cli_add_login": "Логин Steam: ",
        "cli_add_password": "Пароль Steam (ввод скрыт): ",
        "cli_add_shared_secret": "Shared secret (ввод скрыт): ",
        "cli_add_verified_prompt": (
            "Подтверждаете, что вручную проверили данные и имеете право "
            "добавить этот аккаунт? Введите ДА или YES: "
        ),
        "cli_add_verification_required": (
            "Без ручной проверки аккаунт не добавлен. Автоматический вход в Steam "
            "не выполнялся."
        ),
        "cli_add_steamid": "SteamID64 (необязательно): ",
        "cli_add_dota_id": "ID аккаунта Dota (необязательно): ",
        "cli_add_mmr": "Текущий MMR (необязательно): ",
        "cli_add_behavior": "Порядочность (необязательно): ",
        "cli_add_mmr_invalid": "MMR должен быть целым неотрицательным числом",
        "cli_add_behavior_invalid": (
            "Порядочность должна быть целым неотрицательным числом"
        ),
        "cli_add_success": (
            "Аккаунт добавлен с локальным ID {account_id}. Секреты не отображались."
        ),
        "cli_add_next": (
            "Создайте объявление вручную в FunPay, затем запустите register_lot.py "
            "для привязки объявления к аккаунту."
        ),
        "cli_add_failed": "Не удалось добавить аккаунт: {error}",
        "cli_lot_id": "ID лота FunPay: ",
        "cli_lot_title": "Точное название объявления (используется для сопоставления заказа): ",
        "cli_lot_price": "Цена за час аренды: ",
        "cli_lot_account": "Локальный ID аккаунта из add_account.py: ",
        "cli_lot_invalid": "Цена должна быть числом, а ID аккаунта — целым числом",
        "cli_lot_success": (
            "Объявление зарегистрировано. Заказ с него зарезервирует только "
            "связанный аккаунт."
        ),
        "cli_lot_failed": "Не удалось зарегистрировать объявление: {error}",
        "cli_preview_account": "Локальный ID аккаунта: ",
        "cli_preview_price": "Цена за час: ",
        "cli_preview_missing": (
            "Аккаунт не найден или сейчас недоступен (не свободен либо есть VAC-ban)."
        ),
        "cli_preview_mmr_required": (
            "Для заголовка укажите MMR при добавлении аккаунта либо обновите его "
            "в базе после ручной проверки."
        ),
        "cli_preview_title": "Заголовок:",
        "cli_preview_description": "Описание:",
        "cli_preview_publish_warning": (
            "Это только предпросмотр: текст автоматически не публикуется. "
            "Создайте лот вручную в FunPay, затем привяжите его через "
            "python register_lot.py."
        ),
        "cli_preview_failed": "Не удалось подготовить текст: {error}",
        "listing_title_template": (
            "🔱【АРЕНДА】🔱【1+ ЧАС】🔱【{mmr} MMR】🔱"
            "【{behavior} ПОРЯДОЧНОСТЬ】🔱【РЕЙТИНГ】| 1 ЧАС | Dota {mmr}"
        ),
        "listing_behavior_unknown": "не указана",
        "listing_description_template": (
            "Аренда аккаунта Dota 2 на выбранное количество часов.\n\n"
            "📊 MMR: {mmr}\n"
            "🤝 Порядочность: {behavior}\n"
            "💰 Цена: {price} за час\n"
            "Значения указаны оператором вручную, могут измениться и не "
            "проверяются автоматически.\n\n"
            "⚠️ Выберите нужное количество часов при оплате: например, 1 "
            "единица — 1 час, 3 единицы — 3 часа.\n"
            "После покупки заказ обрабатывается оператором вручную. "
            "Автоматическая выдача данных не поддерживается.\n\n"
            "Разрешено: менять имя и аватар, играть в доступные режимы.\n\n"
            "Запрещено: читы, скрипты и другие нарушения правил игры; "
            "изменение данных аккаунта; порча матчей и токсичное поведение.\n\n"
            "Доступ предоставляется на срок аренды и не является передачей "
            "аккаунта в исключительное пользование. Для вопросов по заказу "
            "обратитесь к оператору.\n"
        ),
        "admin_menu_title": "Панель управления арендой",
        "admin_menu_status": "📊 Статус",
        "admin_menu_accounts": "👥 Аккаунты",
        "admin_menu_rentals": "🕒 Активные аренды",
        "admin_menu_lots": "🛍 Объявления",
        "admin_menu_add_account": "➕ Добавить аккаунт",
        "admin_menu_listing_text": "📝 Текст объявления",
        "admin_menu_settings": "⚙️ Настройки",
        "admin_menu_open": "Откройте раздел:",
        "admin_menu_unauthorized": "Это меню доступно только администратору.",
        "admin_menu_status_text": (
            "Статус базы:\n"
            "Аккаунты всего: {accounts_total}\n"
            "Свободно: {accounts_free}\n"
            "В аренде: {accounts_rented}\n"
            "Обслуживание: {accounts_maintenance}\n"
            "Заблокировано: {accounts_banned}\n"
            "VAC-ban: {vac_banned}\n"
            "Активные аренды: {active_rentals}\n"
            "Истекли, ожидают обработки: {expired_unreleased}\n"
            "Объявления: {lots_total} (без привязки: {unlinked_accounts})\n"
            "Ручные задачи: {manual_tasks}"
        ),
        "admin_menu_accounts_empty": "Аккаунтов пока нет.",
        "admin_menu_account_row": (
            "№{account_id} — {status}; MMR: {mmr}; VAC: {vac}; лот: {lot}"
        ),
        "admin_menu_vac_yes": "бан",
        "admin_menu_vac_no": "нет",
        "admin_menu_no_lot": "не привязан",
        "admin_menu_rentals_empty": "Активных аренд нет.",
        "admin_menu_rental_row": (
            "Заказ №{order_id}; покупатель: {buyer}; аккаунт №{account_id}; "
            "лот: {lot_id}; до: {ends_at}"
        ),
        "admin_menu_lots_empty": "Объявления ещё не привязаны.",
        "admin_menu_lot_row": (
            "Лот {lot_id}: {title}; {price}/час; аккаунт: {account}"
        ),
        "admin_menu_add_account_text": (
            "Секреты нельзя безопасно вводить в Telegram. На компьютере, где "
            "находится база бота, выполните `python add_account.py`. Пароль и "
            "shared secret вводятся скрыто и сохраняются зашифрованными. "
            "Затем создайте объявление вручную в FunPay и привяжите его через "
            "`python register_lot.py`."
        ),
        "admin_menu_listing_text": (
            "Для предпросмотра заголовка и описания выполните на компьютере "
            "с базой `python prepare_listing.py`. Используются только вручную "
            "введённые MMR/порядочность; вход в Steam и публикация не выполняются."
        ),
        "admin_menu_settings_text": (
            "Настройки (значения секретов скрыты):\n"
            "FunPay: {funpay}\nTelegram-уведомления: {telegram}\n"
            "Ключ шифрования: {encryption}\nSteam API: {steam_api}\n"
            "База: {db_path}\nЯзык: {language}\n\n"
            "Чтобы изменить параметры, отредактируйте `.env` на компьютере "
            "с ботом и перезапустите процесс."
        ),
        "admin_menu_configured": "настроено",
        "admin_menu_missing": "не настроено",
        "admin_menu_back": "↩️ В меню",
        "admin_status_free": "свободен",
        "admin_status_rented": "в аренде",
        "admin_status_banned": "заблокирован",
        "admin_status_maintenance": "обслуживание",
        "admin_menu_not_configured": (
            "Админ-меню не запущено: задайте TG_BOT_TOKEN и числовой TG_ADMIN_ID."
        ),
        "admin_menu_poll_conflict": (
            "Telegram не разрешил получать обновления. Убедитесь, что этот токен "
            "не используется другим long-polling процессом и для бота не настроен webhook."
        ),
        "admin_menu_poll_failed": "Ошибка Telegram admin-меню (%s)",
        "admin_menu_api_failed": "Telegram API отклонил запрос: {method}",
    },
    "en": {
        "order_already_registered": "This order has already been registered.",
        "paid_order_operator": "Payment received. Your order has been referred to an operator.",
        "extension_operator": "Payment received. An operator needs to review this order.",
        "extension_confirmed": "Rental extended by {hours} h. Access ends: {ends}.",
        "already_renting": (
            "Payment received. You already have an active order; please contact an operator."
        ),
        "no_accounts": (
            "Payment received. No account is currently available; please contact an operator."
        ),
        "manual_fulfillment": (
            "Payment received and order registered. Please contact an operator "
            "for further assistance."
        ),
        "credential_request_active": (
            "Automatic delivery of account details and codes is disabled. "
            "Please contact an operator."
        ),
        "credential_request_inactive": "No active rental was found for this chat.",
        "notify_lot_unmatched": (
            "Could not match paid order #{order_id} to a configured lot."
        ),
        "notify_extension_unmatched": (
            "Paid extension order #{order_id} has no active rental."
        ),
        "notify_buyer_already_renting": (
            "Paid order #{order_id}: the buyer already has an active rental."
        ),
        "notify_no_accounts": (
            "Paid order #{order_id}: no account is currently available."
        ),
        "notify_order_failed": (
            "Could not register paid order #{order_id}; operator action is required."
        ),
        "notify_manual_fulfillment": (
            "Order #{order_id} is registered for account #{account_id}; "
            "automated credential delivery is disabled."
        ),
        "notify_password_manual": (
            "Rental ended: account #{account_id} requires a manual password review."
        ),
        "notify_vac_disabled": (
            "Steam VAC check skipped because STEAM_API_KEY is not configured."
        ),
        "notify_vac_banned": (
            "Accounts with a VAC ban were removed from the pool. SteamID: {steam_id}."
        ),
        "notify_vac_failed": "Steam VAC check failed; see the application log.",
        "notify_mmr_failed": (
            "OpenDota MMR check failed for account #{account_id}."
        ),
        "digest_warning_title": "⚠️ Warning digest:",
        "digest_critical_title": "🚨 Notification digest:",
        "severity_warning": "warning",
        "severity_critical": "critical",
        "telegram_credentials_missing": (
            "TG_BOT_TOKEN and TG_ADMIN_ID are required to send Telegram notifications"
        ),
        "funpay_key_missing": "FUNPAY_GOLDEN_KEY must be configured",
        "secret_key_missing": "SECRET_KEY must contain a Fernet key",
        "telegram_rejected": "Telegram rejected the notification",
        "telegram_digest_failed": "Could not send notification digest (%s)",
        "telegram_critical_failed": (
            "Could not immediately send critical notification (%s)"
        ),
        "telegram_password_task": (
            "Account #{account_id} requires a manual password review "
            "(task #{task_id}). No automatic password or email access was performed."
        ),
        "telegram_password_task_failed": (
            "Could not notify the administrator about a password review task (%s)"
        ),
        "ticker_failed": "Rental expiry check failed (%s)",
        "funpay_started": "FunPay event listener started",
        "funpay_handler_failed": "FunPay event handler failed (%s)",
        "funpay_cookie_refresh": "FunPay rejected the session cookie; refreshing session",
        "daily_vac_failed": "Steam VAC check failed (%s)",
        "daily_mmr_failed": "OpenDota MMR check failed for account #%s (%s)",
        "daily_checks_failed": "Daily account checks failed (%s)",
        "steam_response_invalid": "Steam bans response has no players list",
        "cli_add_login": "Steam account login: ",
        "cli_add_password": "Steam password (input hidden): ",
        "cli_add_shared_secret": "Shared secret (input hidden): ",
        "cli_add_verified_prompt": (
            "Confirm you manually checked the details and are authorized to add "
            "this account? Type YES or ДА: "
        ),
        "cli_add_verification_required": (
            "Account was not added without manual verification. No Steam sign-in "
            "was performed."
        ),
        "cli_add_steamid": "SteamID64 (optional): ",
        "cli_add_dota_id": "Dota account ID (optional): ",
        "cli_add_mmr": "Current MMR (optional): ",
        "cli_add_behavior": "Behavior score (optional): ",
        "cli_add_mmr_invalid": "MMR must be a non-negative whole number",
        "cli_add_behavior_invalid": "Behavior score must be a non-negative whole number",
        "cli_add_success": "Account added with local ID {account_id}. Secrets were not displayed.",
        "cli_add_next": (
            "Create its FunPay listing manually, then run register_lot.py "
            "to bind the listing to this account."
        ),
        "cli_add_failed": "Could not add account: {error}",
        "cli_lot_id": "FunPay lot ID: ",
        "cli_lot_title": "Exact listing title (used to match orders): ",
        "cli_lot_price": "Price per rental hour: ",
        "cli_lot_account": "Local account ID from add_account.py: ",
        "cli_lot_invalid": "Price must be numeric and account ID must be an integer",
        "cli_lot_success": (
            "Listing registered. Paid orders for this listing will reserve only "
            "its linked account."
        ),
        "cli_lot_failed": "Could not register listing: {error}",
        "cli_preview_account": "Local account ID: ",
        "cli_preview_price": "Hourly price: ",
        "cli_preview_missing": (
            "Account not found or unavailable (not free or VAC-banned)."
        ),
        "cli_preview_mmr_required": (
            "Enter MMR when adding the account or update it in the database "
            "after manual verification."
        ),
        "cli_preview_title": "Title:",
        "cli_preview_description": "Description:",
        "cli_preview_publish_warning": (
            "Preview only: this text is not published automatically. Create the "
            "listing manually on FunPay, then link it with python register_lot.py."
        ),
        "cli_preview_failed": "Could not prepare listing text: {error}",
        "listing_title_template": (
            "🔱【RENTAL】🔱【1+ HOUR】🔱【{mmr} MMR】🔱"
            "【{behavior} BEHAVIOR】🔱【RANKED】| 1 HOUR | Dota {mmr}"
        ),
        "listing_behavior_unknown": "not provided",
        "listing_description_template": (
            "Dota 2 account rental for the number of hours selected.\n\n"
            "📊 MMR: {mmr}\n"
            "🤝 Behavior score: {behavior}\n"
            "💰 Price: {price} per hour\n"
            "Values are entered manually by the operator, may change, and are "
            "not automatically verified.\n\n"
            "⚠️ Select the number of hours when paying: for example, 1 unit is "
            "1 hour and 3 units are 3 hours.\n"
            "After purchase, an operator handles the order manually. Automatic "
            "credential delivery is not supported.\n\n"
            "Allowed: change name and avatar, play available modes.\n\n"
            "Prohibited: cheats, scripts, and other game-rule violations; "
            "changing account details; griefing and toxic behavior.\n\n"
            "Access is for the rental period and is not an exclusive transfer "
            "of the account. Contact the operator with order questions.\n"
        ),
        "admin_menu_title": "Rental management",
        "admin_menu_status": "📊 Status",
        "admin_menu_accounts": "👥 Accounts",
        "admin_menu_rentals": "🕒 Active rentals",
        "admin_menu_lots": "🛍 Listings",
        "admin_menu_add_account": "➕ Add account",
        "admin_menu_listing_text": "📝 Listing text",
        "admin_menu_settings": "⚙️ Settings",
        "admin_menu_open": "Choose a section:",
        "admin_menu_unauthorized": "This menu is available to the administrator only.",
        "admin_menu_status_text": (
            "Database status:\n"
            "Accounts total: {accounts_total}\n"
            "Free: {accounts_free}\n"
            "Rented: {accounts_rented}\n"
            "Maintenance: {accounts_maintenance}\n"
            "Banned: {accounts_banned}\n"
            "VAC-banned: {vac_banned}\n"
            "Active rentals: {active_rentals}\n"
            "Expired, awaiting processing: {expired_unreleased}\n"
            "Listings: {lots_total} (unlinked accounts: {unlinked_accounts})\n"
            "Manual tasks: {manual_tasks}"
        ),
        "admin_menu_accounts_empty": "No accounts have been added.",
        "admin_menu_account_row": (
            "#{account_id} — {status}; MMR: {mmr}; VAC: {vac}; listing: {lot}"
        ),
        "admin_menu_vac_yes": "banned",
        "admin_menu_vac_no": "no",
        "admin_menu_no_lot": "not linked",
        "admin_menu_rentals_empty": "No active rentals.",
        "admin_menu_rental_row": (
            "Order #{order_id}; buyer: {buyer}; account #{account_id}; "
            "listing: {lot_id}; until: {ends_at}"
        ),
        "admin_menu_lots_empty": "No listings have been linked yet.",
        "admin_menu_lot_row": (
            "Listing {lot_id}: {title}; {price}/hour; account: {account}"
        ),
        "admin_menu_add_account_text": (
            "Secrets cannot be safely entered through Telegram. On the computer "
            "hosting the bot database, run `python add_account.py`. Password and "
            "shared secret are hidden during input and stored encrypted. Then "
            "create the listing manually on FunPay and link it with "
            "`python register_lot.py`."
        ),
        "admin_menu_listing_text": (
            "To preview the listing title and description, run "
            "`python prepare_listing.py` on the computer hosting the database. "
            "Only manually entered MMR/behavior data is used; there is no Steam "
            "sign-in or publication."
        ),
        "admin_menu_settings_text": (
            "Settings (secret values are hidden):\n"
            "FunPay: {funpay}\nTelegram notifications: {telegram}\n"
            "Encryption key: {encryption}\nSteam API: {steam_api}\n"
            "Database: {db_path}\nLanguage: {language}\n\n"
            "To change settings, edit `.env` on the bot computer and restart "
            "the process."
        ),
        "admin_menu_configured": "configured",
        "admin_menu_missing": "not configured",
        "admin_menu_back": "↩️ Menu",
        "admin_status_free": "free",
        "admin_status_rented": "rented",
        "admin_status_banned": "banned",
        "admin_status_maintenance": "maintenance",
        "admin_menu_not_configured": (
            "Admin menu is inactive: configure TG_BOT_TOKEN and numeric TG_ADMIN_ID."
        ),
        "admin_menu_poll_conflict": (
            "Telegram updates could not be polled. Make sure this token is not used "
            "by another long-polling process and no webhook is configured."
        ),
        "admin_menu_poll_failed": "Telegram admin menu polling failed (%s)",
        "admin_menu_api_failed": "Telegram API rejected request: {method}",
    },
}

_SEVERITY_KEYS = {
    "warning": "severity_warning",
    "critical": "severity_critical",
}

if Config.BOT_LANGUAGE not in _MESSAGES:
    raise ValueError(
        f"Unsupported BOT_LANGUAGE {Config.BOT_LANGUAGE!r}; choose 'ru' or 'en'"
    )


def tr(key: str, **values) -> str:
    """Return a localized interface message for the configured bot language."""
    try:
        message = _MESSAGES[Config.BOT_LANGUAGE][key]
    except KeyError as exc:
        raise KeyError(f"Missing translation: {key}") from exc
    return message.format(**values) if values else message


def severity_label(severity: str) -> str:
    key = _SEVERITY_KEYS.get(severity)
    return tr(key) if key else severity
