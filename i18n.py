from config import Config

_MESSAGES = {
    "ru": {
        "order_already_registered": "Этот заказ уже зарегистрирован.",
        "paid_order_operator": "Оплата получена. Заказ передан оператору.",
        "extension_operator": "Оплата получена. Для этого заказа требуется оператор.",
        "extension_confirmed": "Аренда продлена на {hours} ч. Доступ до: {ends}.",
        "extension_command_usage": "Для продления отправьте команду /dodep без параметров.",
        "extension_request_unavailable": (
            "Не удалось открыть окно продления: активная аренда не найдена "
            "или её срок уже истёк. Обратитесь к оператору."
        ),
        "extension_payment_link": (
            "Ссылка на лот для продления:\n{link}\n"
            "Оплатите выбранное количество часов до {expires}. "
            "Срок продлится только после подтверждения оплаты; 10-минутное "
            "окно не добавляет оплачиваемое время."
        ),
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
        "profile_screenshot_request": (
            "После того как оператор предоставит доступ, отправьте сюда скрин "
            "профиля Dota 2. Администратор вручную проверит MMR, порядочность и "
            "видимые признаки читов. Фото будет храниться в Telegram у "
            "администратора и может быть размещено в объявлении после проверки. "
            "Отправляя его, вы соглашаетесь на это. Не включайте логин, пароль, "
            "почту, коды или личную переписку."
        ),
        "profile_screenshot_no_active_rental": (
            "Скриншот профиля принимается только в чате с активной арендой."
        ),
        "profile_screenshot_admin_unavailable": (
            "Сейчас передать скриншот на проверку не удалось. Свяжитесь с оператором."
        ),
        "profile_screenshot_invalid": (
            "Не удалось безопасно обработать изображение. Отправьте скриншот "
            "как изображение прямо в этом FunPay-чате."
        ),
        "profile_screenshot_admin_caption": (
            "Скрин профиля — заказ №{order_id}\n"
            "Покупатель FunPay: {buyer}\n"
            "Дата: {submitted_at}\n"
            "Лот: {lot_id}\n\n"
            "Проверьте вручную MMR, порядочность и видимые признаки читов. "
            "При сомнениях не используйте скрин в объявлении. "
            "Используйте публично только с согласием покупателя. "
            "Автораспознавание не выполняется; фото на лоте заменяется вручную."
        ),
        "profile_screenshot_delivery_failed": (
            "Не удалось сохранить скриншот заказа №{order_id} в Telegram "
            "(ошибка {error})."
        ),
        "profile_screenshot_delivery_failed_buyer": (
            "Не получилось передать скриншот администратору. Пожалуйста, "
            "повторите отправку или свяжитесь с оператором."
        ),
        "profile_screenshot_received": (
            "Скриншот получен и передан администратору для ручной проверки."
        ),
        "credential_request_active": (
            "Автоматическая выдача кодов и данных аккаунта отключена. "
            "Обратитесь к оператору."
        ),
        "credential_request_inactive": "Активная аренда для этого чата не найдена.",
        "available_lots_empty": "Сейчас свободных лотов нет.",
        "available_lots_usage": "Используйте /akk для списка или /akk <ID_лота>, чтобы получить ссылку.",
        "available_lots_changed": "Этот вариант уже недоступен. Отправьте /akk, чтобы обновить список.",
        "available_lots_header": "Доступные лоты (цена указана за 1 час):",
        "available_lots_continued": "Доступные лоты (продолжение):",
        "available_lots_footer": "Чтобы получить ссылку, отправьте /akk <ID_лота>.",
        "available_lot_row": "{lot_id}. {title} · MMR: {mmr} · {price} за час",
        "available_lot_link": (
            "Лот {lot_id}:\n{link}\n"
            "Количество единиц при заказе соответствует часам аренды."
        ),
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
        "cli_add_steamid": "SteamID64 (необязательно): ",
        "cli_add_dota_id": "ID аккаунта Dota (необязательно): ",
        "cli_add_dota_required": (
            "Для автоматического обновления MMR укажите ID аккаунта Dota."
        ),
        "cli_add_dota_invalid": "ID аккаунта Dota должен состоять из цифр",
        "cli_add_mmr": "Текущий MMR (необязательно): ",
        "cli_add_behavior": "Порядочность (необязательно): ",
        "cli_add_lot_id": (
            "ID уже созданного лота FunPay для этого аккаунта "
            "(Enter — привязать позже): "
        ),
        "cli_lot_account_choice": (
            "Локальный ID аккаунта для привязки к этому лоту: "
        ),
        "cli_lot_accounts_empty": (
            "Нет свободных аккаунтов без привязанного лота. Сначала добавьте "
            "карточку через Telegram."
        ),
        "cli_lot_accounts_header": (
            "Свободные аккаунты без лота (локальный ID / Dota ID / MMR / "
            "порядочность):"
        ),
        "cli_lot_id_invalid": (
            "Отправьте числовой ID лота или HTTPS-ссылку на лот FunPay."
        ),
        "cli_lot_already_registered": "Этот лот уже привязан к аккаунту",
        "cli_lot_fetch_failed": (
            "Не удалось получить данные лота FunPay. Проверьте ID и "
            "FUNPAY_GOLDEN_KEY."
        ),
        "cli_lot_link_success": (
            "Лот {lot_id} автоматически привязан к аккаунту #{account_id}; "
            "название и цена получены из FunPay."
        ),
        "listing_sync_failed": (
            "Не удалось обновить объявление {lot_id}; проверьте сессию FunPay."
        ),
        "listing_sync_missing_mmr": (
            "Лот {lot_id} не обновлён: для аккаунта #{account_id} пока нет MMR."
        ),
        "cli_listing_sync_failed": (
            "Не удалось синхронизировать объявление: {error}"
        ),
        "cli_listing_link_prompt": (
            "Связать с лотом сейчас? Введите его ID или нажмите Enter: "
        ),
        "cli_listing_sync_enabled": (
            "Заголовок и описание лота будут автоматически обновляться по "
            "данным аккаунта."
        ),
        "cli_add_mmr_invalid": "MMR должен быть целым неотрицательным числом",
        "cli_add_behavior_invalid": (
            "Порядочность должна быть целым неотрицательным числом"
        ),
        "cli_behavior_account": "Локальный ID аккаунта: ",
        "cli_behavior_value": "Новая порядочность после ручной проверки: ",
        "cli_behavior_invalid": (
            "Порядочность должна быть целым неотрицательным числом"
        ),
        "cli_behavior_updated": (
            "Порядочность сохранена в базе."
        ),
        "cli_behavior_listing_updated": (
            "Заголовок и описание привязанного лота автоматически обновлены."
        ),
        "cli_behavior_waiting_mmr": (
            "Лот привязан, но MMR пока неизвестен. После первой оценки OpenDota "
            "бот заполнит объявление автоматически."
        ),
        "cli_behavior_update_failed": (
            "Значение сохранено в базе, но лот {lot_id} не обновлён. "
            "Проверьте сессию FunPay; бот повторит синхронизацию при запуске."
        ),
        "cli_add_success": (
            "Аккаунт добавлен с локальным ID {account_id}. Секреты не отображались."
        ),
        "cli_add_next": (
            "Создайте лот в FunPay и выполните python register_lot.py, чтобы "
            "привязать его к этому аккаунту."
        ),
        "cli_add_failed": "Не удалось добавить аккаунт: {error}",
        "cli_lot_id": "ID лота или HTTPS-ссылка FunPay: ",
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
            "Это только предпросмотр. Создайте лот в FunPay один раз и привяжите "
            "его через python register_lot.py; после привязки бот синхронизирует "
            "заголовок и описание."
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
            "MMR обновляется автоматически по оценке OpenDota. Порядочность "
            "указана оператором вручную; фактические значения могут измениться.\n\n"
            "⚠️ Выберите нужное количество часов при оплате: например, 1 "
            "единица — 1 час, 3 единицы — 3 часа.\n"
            "После покупки заказ обрабатывается оператором вручную. "
            "Автоматическая выдача данных не поддерживается.\n\n"
            "После предоставления доступа отправьте скрин профиля Dota 2 в этот "
            "FunPay-чат. Администратор вручную проверит MMR, порядочность и "
            "видимые признаки читов. Скрин будет храниться в Telegram у "
            "администратора и может быть размещён в объявлении после проверки; "
            "отправляя его, вы соглашаетесь на это. Не включайте логин, пароль, "
            "почту, коды или личную переписку.\n\n"
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
        "admin_menu_link_lot": "🔗 Привязать лот",
        "admin_menu_update_behavior": "🤝 Обновить порядочность",
        "admin_menu_sync_listings": "🔄 Обновить лоты",
        "admin_menu_edit_account": "✏️ Данные аккаунта",
        "admin_menu_edit_lot_price": "💰 Цена лота",
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
            "Отправьте одной строкой: Dota ID [MMR] [порядочность]. "
            "Пример: `1232330009 - 10334`. MMR и порядочность можно пропустить "
            "или указать как `-`. Логин, пароль и коды сюда не отправляйте."
        ),
        "admin_menu_add_account_invalid": (
            "Формат: Dota ID [MMR] [порядочность]. Нужен числовой Dota ID; "
            "MMR — 0–15000, порядочность — 0–12000. Не отправляйте пароли или коды."
        ),
        "admin_menu_add_account_duplicate": (
            "Этот профиль уже есть в списке как аккаунт №{account_id}. "
            "Повторная карточка не создана."
        ),
        "admin_menu_add_account_verified": (
            "Профиль найден через {sources}. Карточка аккаунта создана: "
            "№{account_id}.\n"
            "Dota ID: {dota_id}\n"
            "SteamID64: {steamid64}\n"
            "Имя Steam: {profile_name}\n"
            "Профиль Steam: {visibility}\n"
            "MMR: {mmr}; rank_tier: {rank_tier}\n"
            "SteamDB ID finder: {steamdb_url}\n"
            "Пароли и коды не запрашивались и не сохранялись."
        ),
        "admin_menu_add_account_not_found": (
            "OpenDota не нашёл профиль с таким Dota ID. Карточка не создана. "
            "Проверьте ID профиля Dota 2 и отправьте его снова."
        ),
        "admin_menu_add_account_check_unavailable": (
            "Не удалось подтвердить профиль через OpenDota (сеть или API "
            "временно недоступны). Карточка не создана; попробуйте позже."
        ),
        "admin_menu_add_account_saved": (
            "Карточка аккаунта создана: №{account_id}. Секреты не запрашивались "
            "и не сохранялись. При необходимости измените несекретные поля и "
            "привяжите лот через меню «Аккаунты»."
        ),
        "admin_profile_visibility_public": "открытый",
        "admin_profile_visibility_private": "закрытый",
        "admin_profile_visibility_friends": "только для друзей",
        "admin_profile_visibility_unknown": "не удалось определить",
        "admin_profile_visibility_not_configured": (
            "не проверен: укажите STEAM_API_KEY в .env"
        ),
        "admin_menu_listing_text": (
            "Текущие значения MMR/порядочности и связанные лоты:\n"
            "{stats}\n\n"
            "MMR обновляется по OpenDota; после изменения заголовок и описание "
            "лота обновятся автоматически. Для ручного изменения порядочности "
            "нажмите «Обновить порядочность»."
        ),
        "admin_menu_link_enter_lot": (
            "Отправьте ID или HTTPS-ссылку на уже созданный лот FunPay. "
            "Название и цена будут получены автоматически; цену бот не меняет."
        ),
        "admin_menu_link_no_accounts": (
            "Нет свободных аккаунтов без привязанного лота. Сначала добавьте "
            "карточку без секретов через меню «Добавить аккаунт»."
        ),
        "admin_menu_link_choose_account": (
            "Выберите свободный аккаунт для этого лота:"
        ),
        "admin_menu_dota_enter": (
            "Для автоматического MMR введите цифровой ID аккаунта Dota "
            "для аккаунта #{account_id}."
        ),
        "admin_menu_linked": (
            "Лот {lot_id} привязан к аккаунту #{account_id}. Заголовок и описание "
            "синхронизируются автоматически."
        ),
        "admin_menu_behavior_choose": (
            "Выберите аккаунт, для которого вручную проверена новая порядочность:"
        ),
        "admin_menu_behavior_enter": (
            "Введите проверенное значение порядочности для аккаунта #{account_id} "
            "(целое число от 0 до 12000)."
        ),
        "admin_menu_behavior_invalid": (
            "Введите целое число от 0 до 12000. Для отмены отправьте /cancel."
        ),
        "admin_menu_behavior_saved": (
            "Порядочность сохранена; привязанный лот обновлён."
        ),
        "admin_menu_behavior_saved_pending": (
            "Порядочность сохранена. Если лот привязан, он будет синхронизирован "
            "при восстановлении соединения с FunPay."
        ),
        "admin_menu_sync_done": (
            "Синхронизация завершена. Обновлено лотов: {updated}."
        ),
        "admin_menu_funpay_unavailable": (
            "FunPay ещё не подключён. Дождитесь соединения и повторите."
        ),
        "admin_menu_action_expired": (
            "Действие отменено или устарело. Откройте нужный пункт меню заново."
        ),
        "admin_menu_cancelled": "Действие отменено.",
        "admin_menu_operation_failed": (
            "Не удалось выполнить действие в админ-меню (%s)"
        ),
        "admin_menu_operation_failed_text": (
            "Действие не выполнено. Проверьте ID лота, подключение FunPay и "
            "состояние аккаунта."
        ),
        "admin_menu_listing_stats": (
            "Лот {lot_id}; аккаунт #{account_id}; MMR: {mmr}; порядочность: {behavior}"
        ),
        "admin_menu_edit_account_choose": (
            "Выберите аккаунт для изменения несекретных полей:"
        ),
        "admin_menu_edit_account_fields": (
            "Данные аккаунта #{account_id}: SteamID64 {steamid}; Dota ID {dota_id}; "
            "MMR {mmr}; порядочность {behavior}.\n"
            "Выберите поле для изменения. Пароли и shared secret здесь не "
            "показываются и не редактируются."
        ),
        "admin_menu_field_steamid64": "SteamID64",
        "admin_menu_field_dota_id": "Dota ID",
        "admin_menu_field_dota_account_id": "Dota ID",
        "admin_menu_field_mmr": "MMR",
        "admin_menu_field_behavior": "Порядочность",
        "admin_menu_field_behavior_score": "Порядочность",
        "admin_menu_field_enter": (
            "Введите новое значение «{field}» для аккаунта #{account_id}. "
            "Для отмены отправьте /cancel."
        ),
        "admin_menu_field_invalid": (
            "Неверное значение. ID должны состоять из цифр; SteamID64 — ровно "
            "17 цифр, MMR — 0–15000, порядочность — 0–12000."
        ),
        "admin_menu_field_saved": (
            "Данные аккаунта сохранены. Изменения текста лота синхронизируются "
            "при следующем подключении FunPay."
        ),
        "admin_menu_field_saved_synced": (
            "Данные аккаунта и связанный текст лота обновлены."
        ),
        "admin_menu_field_saved_pending": (
            "Данные сохранены. Связанный текст лота пока не обновился; бот "
            "повторит синхронизацию после восстановления FunPay."
        ),
        "admin_menu_edit_lot_price_choose": "Выберите лот для изменения цены:",
        "admin_menu_price_enter": (
            "Введите новую цену лота {lot_id} за единицу в FunPay "
            "(число больше 0, максимум 100000)."
        ),
        "admin_menu_price_saved": (
            "Цена лота {lot_id} обновлена до {price}. Синхронизация текста "
            "выполнена, если для неё доступны данные аккаунта и FunPay."
        ),
        "admin_menu_settings_text": (
            "Настройки (значения секретов скрыты):\n"
            "FunPay: {funpay}\nTelegram-уведомления: {telegram}\n"
            "Steam API: {steam_api}\n"
            "База: {db_path}\nЯзык: {bot_language}\n\n"
            "Чтобы изменить параметры, отредактируйте `.env` на компьютере "
            "с ботом и перезапустите процесс."
        ),
        "admin_menu_configured": "настроено",
        "admin_menu_missing": "не настроено",
        "cli_add_use_telegram": (
            "Добавляйте карточки через Telegram: «Добавить аккаунт». "
            "Скрипт больше не запрашивает и не хранит логин, пароль, почту "
            "или Steam Guard secret."
        ),
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
        "extension_command_usage": "Send /dodep without arguments to request an extension.",
        "extension_request_unavailable": (
            "Could not open an extension payment window: no active rental was "
            "found or it has already expired. Please contact the operator."
        ),
        "extension_payment_link": (
            "Extension listing:\n{link}\n"
            "Pay for the selected number of hours by {expires}. "
            "The rental is extended only after payment is confirmed; the "
            "10-minute window does not add paid time."
        ),
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
        "profile_screenshot_request": (
            "After the operator provides access, send a Dota 2 profile screenshot "
            "here. The administrator will manually check MMR, behavior score, and "
            "visible signs of cheats. The photo will be stored in the administrator's "
            "Telegram and may be used in the listing after review. Sending it means "
            "you agree to this. Do not include login details, passwords, email "
            "addresses, codes, or private chats."
        ),
        "profile_screenshot_no_active_rental": (
            "Profile screenshots are accepted only in a chat with an active rental."
        ),
        "profile_screenshot_admin_unavailable": (
            "The screenshot could not be sent for review right now. Please contact an operator."
        ),
        "profile_screenshot_invalid": (
            "The image could not be processed safely. Send the screenshot as an "
            "image directly in this FunPay chat."
        ),
        "profile_screenshot_admin_caption": (
            "Profile screenshot — order #{order_id}\n"
            "FunPay buyer: {buyer}\n"
            "Date: {submitted_at}\n"
            "Listing: {lot_id}\n\n"
            "Manually check MMR, behavior score, and visible signs of cheats. "
            "Do not use a questionable screenshot in the listing. No OCR is used; "
            "only use it publicly with the buyer's consent. The listing photo "
            "must be replaced manually."
        ),
        "profile_screenshot_delivery_failed": (
            "Could not store the screenshot for order #{order_id} in Telegram "
            "(error {error})."
        ),
        "profile_screenshot_delivery_failed_buyer": (
            "The screenshot could not be delivered to the administrator. Please "
            "send it again or contact the operator."
        ),
        "profile_screenshot_received": (
            "Screenshot received and forwarded to the administrator for manual review."
        ),
        "credential_request_active": (
            "Automatic delivery of account details and codes is disabled. "
            "Please contact an operator."
        ),
        "credential_request_inactive": "No active rental was found for this chat.",
        "available_lots_empty": "There are no available listings right now.",
        "available_lots_usage": "Use /akk for the list or /akk <listing_ID> to get a link.",
        "available_lots_changed": "That option is no longer available. Send /akk to refresh the list.",
        "available_lots_header": "Available listings (price is per hour):",
        "available_lots_continued": "Available listings (continued):",
        "available_lots_footer": "Send /akk <listing_ID> to get a link.",
        "available_lot_row": "{lot_id}. {title} · MMR: {mmr} · {price} per hour",
        "available_lot_link": (
            "Listing {lot_id}:\n{link}\n"
            "The order quantity corresponds to rental hours."
        ),
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
        "cli_add_steamid": "SteamID64 (optional): ",
        "cli_add_dota_id": "Dota account ID (optional): ",
        "cli_add_dota_required": (
            "Enter the Dota account ID to enable automatic MMR updates."
        ),
        "cli_add_dota_invalid": "Dota account ID must contain digits only",
        "cli_add_mmr": "Current MMR (optional): ",
        "cli_add_behavior": "Behavior score (optional): ",
        "cli_add_lot_id": (
            "ID of the existing FunPay listing for this account "
            "(Enter to link later): "
        ),
        "cli_lot_account_choice": "Local account ID to link to this listing: ",
        "cli_lot_accounts_empty": (
            "No free unlinked accounts. Add an account record in Telegram first."
        ),
        "cli_lot_accounts_header": (
            "Free unlinked accounts (local ID / Dota ID / MMR / behavior score):"
        ),
        "cli_lot_id_invalid": (
            "Send a numeric listing ID or an HTTPS link to a FunPay listing."
        ),
        "cli_lot_already_registered": "This listing is already linked to an account",
        "cli_lot_fetch_failed": (
            "Could not fetch the FunPay listing. Check its ID and FUNPAY_GOLDEN_KEY."
        ),
        "cli_lot_link_success": (
            "Listing {lot_id} linked to account #{account_id}; title and price "
            "were fetched from FunPay."
        ),
        "listing_sync_failed": (
            "Could not update listing {lot_id}; check the FunPay session."
        ),
        "listing_sync_missing_mmr": (
            "Listing {lot_id} not updated: account #{account_id} has no MMR yet."
        ),
        "cli_listing_sync_failed": (
            "Could not sync the listing: {error}"
        ),
        "cli_listing_link_prompt": (
            "Link a listing now? Enter its ID or press Enter: "
        ),
        "cli_listing_sync_enabled": (
            "The listing title and description will update automatically from "
            "account data."
        ),
        "cli_add_mmr_invalid": "MMR must be a non-negative whole number",
        "cli_add_behavior_invalid": "Behavior score must be a non-negative whole number",
        "cli_behavior_account": "Local account ID: ",
        "cli_behavior_value": "New behavior score after manual verification: ",
        "cli_behavior_invalid": "Behavior score must be a non-negative whole number",
        "cli_behavior_updated": (
            "Behavior score saved to the database."
        ),
        "cli_behavior_listing_updated": (
            "The linked listing title and description were updated automatically."
        ),
        "cli_behavior_waiting_mmr": (
            "The listing is linked, but MMR is not known yet. OpenDota will "
            "populate the listing after the first estimate."
        ),
        "cli_behavior_update_failed": (
            "Value saved to the database, but listing {lot_id} was not updated. "
            "Check the FunPay session; the bot will retry on startup."
        ),
        "cli_add_success": "Account added with local ID {account_id}. Secrets were not displayed.",
        "cli_add_next": (
            "Create the FunPay listing and run python register_lot.py to link "
            "it to this account."
        ),
        "cli_add_failed": "Could not add account: {error}",
        "cli_lot_id": "FunPay listing ID or HTTPS link: ",
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
            "Preview only. Create the listing once on FunPay and link it with "
            "python register_lot.py; the bot will then sync its title and description."
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
            "MMR is automatically updated from the OpenDota estimate. Behavior "
            "score is entered manually; actual values may change.\n\n"
            "⚠️ Select the number of hours when paying: for example, 1 unit is "
            "1 hour and 3 units are 3 hours.\n"
            "After purchase, an operator handles the order manually. Automatic "
            "credential delivery is not supported.\n\n"
            "After the operator provides access, send a Dota 2 profile screenshot "
            "in this FunPay chat. The administrator manually checks the visible "
            "MMR, behavior score, and signs of cheats. The screenshot is stored in "
            "the administrator's Telegram and may be used in the listing after "
            "review; sending it means you agree. Do not include credentials, email "
            "codes, or private chats.\n\n"
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
        "admin_menu_link_lot": "🔗 Link listing",
        "admin_menu_update_behavior": "🤝 Update behavior",
        "admin_menu_sync_listings": "🔄 Sync listings",
        "admin_menu_edit_account": "✏️ Account data",
        "admin_menu_edit_lot_price": "💰 Listing price",
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
            "Send one line: Dota ID [MMR] [behavior score]. Example: "
            "`1232330009 - 10334`. MMR and behavior can be omitted or entered "
            "as `-`. Do not send logins, passwords, or codes here."
        ),
        "admin_menu_add_account_invalid": (
            "Format: Dota ID [MMR] [behavior score]. Dota ID must be numeric; "
            "MMR 0–15000, behavior 0–12000. Do not send passwords or codes."
        ),
        "admin_menu_add_account_duplicate": (
            "This profile is already listed as account #{account_id}. "
            "No duplicate record was created."
        ),
        "admin_menu_add_account_verified": (
            "Profile found through {sources}. Account record created: "
            "#{account_id}.\n"
            "Dota ID: {dota_id}\n"
            "SteamID64: {steamid64}\n"
            "Steam name: {profile_name}\n"
            "Steam profile: {visibility}\n"
            "MMR: {mmr}; rank_tier: {rank_tier}\n"
            "SteamDB ID finder: {steamdb_url}\n"
            "No passwords or codes were requested or stored."
        ),
        "admin_menu_add_account_not_found": (
            "OpenDota did not find a profile for this Dota ID. No account record "
            "was created. Check the Dota 2 profile ID and send it again."
        ),
        "admin_menu_add_account_check_unavailable": (
            "Could not verify the profile through OpenDota (network/API "
            "temporarily unavailable). No account record was created; try later."
        ),
        "admin_menu_add_account_saved": (
            "Account record created: #{account_id}. No secrets were requested "
            "or stored. Edit other non-secret fields or link a listing from the "
            "Accounts menu."
        ),
        "admin_profile_visibility_public": "public",
        "admin_profile_visibility_private": "private",
        "admin_profile_visibility_friends": "friends only",
        "admin_profile_visibility_unknown": "could not determine",
        "admin_profile_visibility_not_configured": (
            "not checked: set STEAM_API_KEY in .env"
        ),
        "admin_menu_listing_text": (
            "Current MMR/behavior values and linked listings:\n"
            "{stats}\n\n"
            "MMR is updated through OpenDota; the listing title and description "
            "then sync automatically. Use “Update behavior” to set a manually "
            "verified behavior score."
        ),
        "admin_menu_edit_account_choose": (
            "Choose an account to edit its non-secret fields:"
        ),
        "admin_menu_edit_account_fields": (
            "Account #{account_id}: SteamID64 {steamid}; Dota ID {dota_id}; "
            "MMR {mmr}; behavior {behavior}.\n"
            "Choose a field to edit. Passwords and shared secrets are never "
            "shown or edited here."
        ),
        "admin_menu_field_steamid64": "SteamID64",
        "admin_menu_field_dota_id": "Dota ID",
        "admin_menu_field_dota_account_id": "Dota ID",
        "admin_menu_field_mmr": "MMR",
        "admin_menu_field_behavior": "Behavior score",
        "admin_menu_field_behavior_score": "Behavior score",
        "admin_menu_field_enter": (
            "Enter the new {field} for account #{account_id}. Send /cancel to abort."
        ),
        "admin_menu_field_invalid": (
            "Invalid value. IDs must contain digits; SteamID64 must be 17 digits, "
            "MMR 0–15000, behavior score 0–12000."
        ),
        "admin_menu_field_saved": (
            "Account data saved. Listing text will sync when FunPay reconnects."
        ),
        "admin_menu_field_saved_synced": (
            "Account data and linked listing text were updated."
        ),
        "admin_menu_field_saved_pending": (
            "Data was saved, but the listing text could not be refreshed. The bot "
            "will retry after FunPay reconnects."
        ),
        "admin_menu_edit_lot_price_choose": "Choose a listing to update its price:",
        "admin_menu_price_enter": (
            "Enter the new FunPay price per unit for listing {lot_id} "
            "(greater than 0, at most 100000)."
        ),
        "admin_menu_price_saved": (
            "Listing {lot_id} price changed to {price}. Text synchronization was "
            "attempted if account data and FunPay are available."
        ),
        "admin_menu_link_enter_lot": (
            "Send the ID or HTTPS link of an existing FunPay listing. Its title "
            "and price will be fetched automatically; the bot does not change the price."
        ),
        "admin_menu_link_no_accounts": (
            "No free unlinked accounts. First add a no-secret account record "
            "from the “Add account” menu."
        ),
        "admin_menu_link_choose_account": (
            "Choose a free account to link to this listing:"
        ),
        "admin_menu_dota_enter": (
            "Enter the numeric Dota account ID for account #{account_id} "
            "to enable automatic MMR updates."
        ),
        "admin_menu_linked": (
            "Listing {lot_id} linked to account #{account_id}. Its title and "
            "description will sync automatically."
        ),
        "admin_menu_behavior_choose": (
            "Choose the account whose behavior score you manually verified:"
        ),
        "admin_menu_behavior_enter": (
            "Enter the verified behavior score for account #{account_id} "
            "(whole number from 0 to 12000)."
        ),
        "admin_menu_behavior_invalid": (
            "Enter a whole number from 0 to 12000. Send /cancel to abort."
        ),
        "admin_menu_behavior_saved": (
            "Behavior score saved; the linked listing was updated."
        ),
        "admin_menu_behavior_saved_pending": (
            "Behavior score saved. If a listing is linked, it will sync when "
            "the FunPay connection is available."
        ),
        "admin_menu_sync_done": (
            "Synchronization complete. Listings updated: {updated}."
        ),
        "admin_menu_funpay_unavailable": (
            "FunPay is not connected yet. Wait for the connection and retry."
        ),
        "admin_menu_action_expired": (
            "This action was cancelled or expired. Start it again from the menu."
        ),
        "admin_menu_cancelled": "Action cancelled.",
        "admin_menu_operation_failed": (
            "Admin menu operation failed (%s)"
        ),
        "admin_menu_operation_failed_text": (
            "Action failed. Check the listing ID, FunPay connection, and account status."
        ),
        "admin_menu_listing_stats": (
            "Listing {lot_id}; account #{account_id}; MMR: {mmr}; behavior: {behavior}"
        ),
        "admin_menu_settings_text": (
            "Settings (secret values are hidden):\n"
            "FunPay: {funpay}\nTelegram notifications: {telegram}\n"
            "Steam API: {steam_api}\n"
            "Database: {db_path}\nLanguage: {bot_language}\n\n"
            "To change settings, edit `.env` on the bot computer and restart "
            "the process."
        ),
        "admin_menu_configured": "configured",
        "admin_menu_missing": "not configured",
        "cli_add_use_telegram": (
            "Add account records in Telegram using “Add account”. This script "
            "no longer requests or stores logins, passwords, email, or Steam "
            "Guard secrets."
        ),
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


def tr_in(language: str, key: str, **values) -> str:
    """Return a localized message in the requested supported language."""
    try:
        message = _MESSAGES[language][key]
    except KeyError as exc:
        raise KeyError(f"Missing translation: {key}") from exc
    return message.format(**values) if values else message


def tr(key: str, **values) -> str:
    """Return a localized interface message for the configured bot language."""
    return tr_in(Config.BOT_LANGUAGE, key, **values)


def severity_label(severity: str) -> str:
    key = _SEVERITY_KEYS.get(severity)
    return tr(key) if key else severity
