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
