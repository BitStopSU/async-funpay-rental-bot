# Async FunPay bot

## Язык сообщений / Message language

Бот поддерживает русский и английский языки для сообщений покупателям и
административных уведомлений. Укажите `BOT_LANGUAGE=ru` или `BOT_LANGUAGE=en`
в файле `.env`. Если параметр не указан, используется русский язык.

The bot supports Russian and English for buyer messages and administrator
notifications. Set `BOT_LANGUAGE=ru` or `BOT_LANGUAGE=en` in `.env`. Russian is
used when the setting is omitted.

## Запуск / Running

Установите зависимости командой `python -m pip install -r requirements.txt`,
скопируйте `.env.example` в `.env`, заполните переменные и запустите
`python main.py`. Для `SECRET_KEY` сгенерируйте ключ Fernet командой
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.

Install dependencies with `python -m pip install -r requirements.txt`, copy
`.env.example` to `.env`, fill in the variables, then run `python main.py`.
Generate a Fernet key for `SECRET_KEY` with
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.

Не добавляйте секреты в этот файл или в систему контроля версий. Автоматическое
получение Steam/email-кодов, вход в аккаунты и смена паролей не поддерживаются;
такие задачи требуют ручной обработки.

Do not put secrets in this file or in version control. Automated access to Steam
or email codes, account sign-in, and password changes are not supported; these
tasks require manual handling.

Бот сохраняет `PHPSESSID` и дополнительную cookie `golden_seal`, которую FunPay
выдаёт при авторизации. Если FunPay отклоняет cookie как устаревшую, бот обновляет
данные сессии и повторяет запрос один раз, не чаще раза в минуту. Если ошибка сохраняется,
проверьте `FUNPAY_GOLDEN_KEY` и войдите в FunPay заново, чтобы получить актуальный ключ.

The bot preserves both `PHPSESSID` and the additional `golden_seal` cookie set by
FunPay during authentication. If FunPay rejects a session cookie as stale, the
bot refreshes its session data and retries the request once, at most once per
minute. If the error persists,
check `FUNPAY_GOLDEN_KEY` and sign in to FunPay again to obtain a fresh key.

## Добавление аккаунтов и объявлений / Accounts and listings

1. Создайте лот в FunPay один раз: установленная версия `aioFunPayAPI` умеет
   редактировать существующие лоты, но не создавать новые.
2. Запустите `python add_account.py`, подтвердите ручную проверку и добавьте
   аккаунт. Для автоматического MMR укажите Dota account ID. Пароль и shared
   secret вводятся скрыто и шифруются Fernet; автоматического входа в Steam нет.
   Введите ID уже созданного лота — бот сам получит из FunPay его название и
   цену и привяжет его к новому аккаунту.
3. Для привязки лота к ранее добавленному аккаунту выполните
   `python register_lot.py`: введите ID лота и выберите аккаунт из списка.
   Вручную вводить название, цену или локальный ID при добавлении нового
   аккаунта не нужно.
4. После привязки бот синхронизирует заголовок и описание при запуске и после
   изменения MMR в ежедневной проверке OpenDota. Цена и остальные поля лота
   не меняются. Порядочность подставляется из базы, но автоматически не
   проверяется: источник её изменения не подключён. После
   ручной проверки нового значения запустите `python update_behavior.py` —
   бот сохранит его и обновит текст привязанного лота.
5. `python prepare_listing.py` оставлен как предпросмотр. Не указывайте в лоте
   логин, пароль, Steam Guard secret или коды. Заказы резервируют только
   связанный аккаунт; обработка заказа остаётся ручной.

Create the FunPay listing once (the installed `aioFunPayAPI` can edit existing
listings but does not support creating them). Run `python add_account.py`, confirm
manual verification, enter the Dota account ID for automatic MMR checks, and
provide the existing listing ID. The bot fetches the title and price from FunPay
and links the listing to the new account; credentials remain hidden and encrypted.
For an account already in the database, run `python register_lot.py`, enter the
listing ID, and choose the account from the list. After linking, the bot updates
the listing title and description on startup and when the daily OpenDota check
changes MMR. It does not change the price or other listing fields. Behavior score
is included from the database but has no automatic data source; after manually
verifying a new score, run `python update_behavior.py` to save it and refresh the
linked listing.
`python prepare_listing.py` remains a preview. Never put credentials or Steam
Guard codes in a listing; order fulfillment remains manual.

## Telegram admin menu / Меню администратора

Укажите `TG_BOT_TOKEN` и числовой Telegram user ID в `TG_ADMIN_ID`, затем
перезапустите `python main.py` и отправьте боту команду `/start` в личном чате.
Inline-меню показывает состояние базы, аккаунты, активные аренды, объявления и
настроенные параметры (секреты не отображаются). Доступ разрешён только ID из
`TG_ADMIN_ID`. Для добавления аккаунта меню направляет к локальной команде
`python add_account.py`: пароль и shared secret нельзя передавать Telegram.

Set `TG_BOT_TOKEN` and your numeric Telegram user ID in `TG_ADMIN_ID`, restart
`python main.py`, and send `/start` to the bot in a private chat. The inline
menu shows database status, accounts, active rentals, listings, and whether
settings are configured without revealing secret values. Only the configured
admin ID is accepted. Account credentials must be entered locally with
`python add_account.py`, not sent through Telegram. Telegram long polling
requires that the same bot token is not already being polled by another process
and that no webhook is configured.

Critical alerts (for example, a newly detected VAC ban) are sent to the
administrator shortly after they are queued. Warning notifications are grouped
into the hourly digest. Both require the Telegram token and admin ID above.

После оплаты бот просит покупателя отправить скрин профиля Dota 2 в FunPay-чат
после получения доступа. Изображение пересылается в личный чат администратора
Telegram с номером заказа, ником и датой; Telegram хранит фото, SQLite сохраняет
только идентификатор сообщения/файла и аудит. Бот принимает изображения только
из HTTPS-ссылок FunPay и не сохраняет их локально. Администратор вручную
проверяет MMR, порядочность и видимые признаки читов; OCR или автоматического
решения нет. Сомнительный скрин не следует использовать. Принятый скрин можно
загрузить на FunPay вручную: установленная библиотека не поддерживает замену
главной картинки лота. Не просите покупателей присылать пароль, код, email или
другие секреты.

After payment, the bot asks the buyer to send a Dota 2 profile screenshot in
the FunPay chat once the operator has provided access. It forwards the image to
the administrator's private Telegram chat with order number, buyer nickname,
and date. Telegram stores the image; SQLite keeps only Telegram message/file
IDs and an audit record. Images are accepted only from HTTPS FunPay links and
are not stored locally. The administrator manually checks MMR, behavior score,
and visible signs of cheats; there is no OCR or automated decision. Do not use
a questionable screenshot. Upload an approved screenshot to the FunPay listing
manually because the installed library does not support replacing a listing's
main image. Never ask buyers for passwords, codes, email, or other secrets.
