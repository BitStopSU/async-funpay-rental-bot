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

1. Запустите `python add_account.py` и подтвердите, что вручную проверили
   информацию и имеете право добавить аккаунт. Бот не пытается войти в Steam и
   не проверяет пароль авторизацией. Пароль и shared secret вводятся скрыто и
   шифруются Fernet перед сохранением в локальную SQLite-базу. MMR и
   порядочность вводятся оператором вручную.
2. Запустите `python prepare_listing.py`, чтобы получить предпросмотр заголовка
   и описания по данным аккаунта и цене. Предпросмотр не публикуется.
3. Создайте объявление вручную в FunPay. В текущей версии `aioFunPayAPI` есть
   редактирование лота, но нет поддерживаемого метода создания нового лота.
   Не указывайте в объявлении логин, пароль, Steam Guard secret или коды.
4. Запустите `python register_lot.py` и укажите ID лота, точное уникальное
   название, почасовую цену и локальный ID аккаунта из первого шага.
5. Для каждого аккаунта повторите шаги. Оплаченный заказ с привязанного лота
   зарезервирует только соответствующий свободный аккаунт. Заказ всё равно
   требует ручного выполнения; бот не входит в Steam и не передаёт секреты.

Run `python add_account.py` and confirm you manually checked the account details
and are authorized to manage the account. The bot does not sign in to Steam or
test credentials by authentication. Password and shared secret are hidden
during entry and encrypted before storage. MMR and behavior score are entered
manually. Run `python prepare_listing.py` for a title and description preview;
it does not publish anything. Create the listing manually (the installed
`aioFunPayAPI` supports editing existing lots, not creating new ones), then run
`python register_lot.py` to bind its ID, exact unique title, hourly price, and
local account ID. Never put credentials or Steam Guard codes in a listing. Paid
orders reserve only the linked account, but fulfillment remains manual.

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
