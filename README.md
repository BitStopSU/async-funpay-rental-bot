# Async FunPay bot

## Язык сообщений / Message language

Бот поддерживает русский и английский языки для сообщений покупателям и
административных уведомлений. Укажите `BOT_LANGUAGE=ru` или `BOT_LANGUAGE=en`
в файле `.env`. Если параметр не указан, используется русский язык.

The bot supports Russian and English for buyer messages and administrator
notifications. Set `BOT_LANGUAGE=ru` or `BOT_LANGUAGE=en` in `.env`. Russian is
used when the setting is omitted.

## Запуск / Running

Для запуска требуется Python 3.10 или новее. Запустите `start.bat` из папки
программы: скрипт создаст виртуальное окружение, установит зависимости и при
первом запуске откроет `.env.example` для настройки. После настройки сохраните
`.env` и нажмите Enter в окне запуска. Для ручного запуска можно выполнить
`python -m pip install -r requirements.txt`, скопировать `.env.example` в
`.env` и запустить `python main.py`. Создавайте карточки аккаунтов в Telegram:
бот принимает только Dota ID и необязательные публичные игровые показатели.
Локальные офлайн-проверки запускаются командой
`python -m unittest discover -s tests -v`; они используют временные базы данных
и поддельные ответы внешних API.

Python 3.10 or newer is required. Run `start.bat` from the program folder: it
creates a virtual environment, installs dependencies, and opens `.env.example`
for configuration on first launch. Save the resulting `.env` and press Enter
in the launcher window. To start manually, install dependencies with
`python -m pip install -r requirements.txt`, copy `.env.example` to `.env`, and
run `python main.py`. Create account records in Telegram; the bot accepts only a
Dota ID and optional public game statistics.
Run offline tests with `python -m unittest discover -s tests -v`; they use
temporary databases and mocked external API responses.

## Windows installer

В GitHub Packages нельзя публиковать произвольный файл `.exe`, поэтому
установщик распространяется в разделе **Releases**. Создайте тег версии вида
`v1.0.0` и отправьте его в GitHub: workflow автоматически соберёт
`AsyncFunPayRentalBot-Setup.exe` и добавит его к релизу. Установщик ставит
файлы в папку пользователя и создаёт ярлыки в меню «Пуск» и на рабочем столе.
Для запуска нужен установленный Python 3.10 или новее; при первом запуске
создаются виртуальное окружение и `.env`. В `.env` нужно указать настройки
Telegram и FunPay.
Если обновляете уже работающего бота, установщик по умолчанию ставит программу
в отдельную папку и создаст новую базу данных. Чтобы сохранить аккаунты и
активные аренды, до первого запуска укажите в `.env` полный путь к прежнему
`rental.db` в `DB_PATH` либо выберите прежнюю папку установки. Остановите
старый процесс перед запуском новой версии.

GitHub Packages does not host arbitrary `.exe` files, so the installer is
distributed from **Releases**. Push a version tag such as `v1.0.0` to GitHub;
the workflow builds `AsyncFunPayRentalBot-Setup.exe` and attaches it to the
release. The installer places the files in the user's profile and creates
Start-menu and optional desktop shortcuts. Python 3.10 or newer must already be
installed. The first launch creates a virtual environment and `.env`; configure
the Telegram and FunPay settings there.
When updating an existing bot, the installer defaults to a separate folder and
would create a new database. To keep accounts and active rentals, set `DB_PATH`
in `.env` to the full path of the existing `rental.db` before the first launch,
or choose the previous installation folder. Stop the old process before starting
the new version.

Не добавляйте секреты в этот файл или в систему контроля версий. Автоматическое
получение Steam/email-кодов, вход в аккаунты и смена паролей не поддерживаются;
такие задачи требуют ручной обработки. При запуске старая схема БД мигрирует:
из таблицы аккаунтов удаляются сохранённые логины и секреты, остальные данные
аккаунтов, аренды и привязки лотов сохраняются.

Do not put secrets in this file or in version control. Automated access to Steam
or email codes, account sign-in, and password changes are not supported; these
tasks require manual handling. On startup, the old database schema is migrated:
stored account logins and secrets are removed while other account data, rentals,
and listing links are preserved.

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
2. Добавьте карточку аккаунта через Telegram: «Добавить аккаунт» и отправьте
   Dota ID, при желании MMR и порядочность, например `1232330009 - 10334`.
   Пароль, email-код и shared secret не нужны боту и не должны отправляться в
   Telegram. Бот не входит в Steam и не проверяет доступ.
3. Для привязки лота к ранее добавленному аккаунту используйте в Telegram
   «Привязать лот»: отправьте ID существующего объявления и выберите аккаунт.
   Либо выполните `python register_lot.py` локально. Вручную вводить название
   и цену при привязке не нужно.
4. После привязки бот синхронизирует заголовок и описание при запуске и после
   изменения MMR в ежедневной проверке OpenDota. Автоматически цена не
   меняется, но администратор может изменить её в Telegram. Порядочность
   подставляется из базы, но автоматически не проверяется: источник её
   изменения не подключён. Её можно обновить в Telegram после ручной проверки
   или запустить `python update_behavior.py`.
5. `python prepare_listing.py` оставлен как предпросмотр. Не указывайте в лоте
   логин, пароль, Steam Guard secret или коды. Заказы резервируют только
   связанный аккаунт; обработка заказа остаётся ручной.

Create the FunPay listing once (the installed `aioFunPayAPI` can edit existing
listings but does not support creating them). Add an account record from Telegram
with its Dota account ID and, optionally, MMR and behavior score, for example
`1232330009 - 10334`. The bot does not need or accept account passwords,
email codes, or shared secrets; it does not sign in to Steam.
For an account already in the database, use Telegram's “Link listing” menu to
send the listing ID and choose the account, or run `python register_lot.py`
locally. After linking, the bot updates
the listing title and description on startup and when the daily OpenDota check
changes MMR. The bot does not automatically change the price, but an admin can
change it in Telegram. Behavior score is included from the database but has no
automatic data source; update it from Telegram after manual verification or run
`python update_behavior.py`.
`python prepare_listing.py` remains a preview. Never put credentials or Steam
Guard codes in a listing; order fulfillment remains manual.

## Rental timing / Срок аренды

Новая аренда длится оплаченные часы плюс один 30-минутный буфер. Продление
добавляет только оплаченные часы к текущему `ends_at`, без повторного буфера и
без смены пароля. Если оплата продления пришла после срока, но до того, как
ticker успел освободить аренду, оплаченные часы считаются с момента продления;
это не позволяет новой аренде сразу истечь.

A new rental lasts the paid hours plus one 30-minute buffer. An extension adds
only the purchased hours to the current `ends_at`, with no second buffer and no
password changes. If an extension is paid after the end time but before the
ticker releases the rental, its purchased time starts at the extension time so
the rental does not expire immediately.

## Telegram admin menu / Меню администратора

Укажите `TG_BOT_TOKEN` и числовой Telegram user ID в `TG_ADMIN_ID`, затем
перезапустите `python main.py` и отправьте боту команду `/start` в личном чате.
Inline-меню показывает состояние базы, аккаунты, активные аренды, объявления и
настроенные параметры (секреты не отображаются). Доступ разрешён только ID из
`TG_ADMIN_ID`. Через меню можно привязать существующий FunPay-лот к выбранному
свободному аккаунту, изменить SteamID64, Dota ID, MMR и вручную проверенную
порядочность, изменить цену существующего лота и запустить синхронизацию
объявлений. ID лота, его название и первоначальная цена получаются из FunPay;
автоматически меняются только заголовок и описание. Новые MMR синхронизируются
из OpenDota ежедневно. Новые лоты создаются на FunPay вручную один раз.

Чтобы добавить карточку, нажмите «Добавить аккаунт» и отправьте Dota ID,
необязательно дополнив его MMR и порядочностью. В Telegram-форме нет полей для
логина, пароля, почты, email-кода или shared secret. Старые зашифрованные
значения удаляются из SQLite при первом запуске новой версии; несекретные
данные аккаунтов, аренды и привязки лотов сохраняются.

Set `TG_BOT_TOKEN` and your numeric Telegram user ID in `TG_ADMIN_ID`, restart
`python main.py`, and send `/start` to the bot in a private chat. The inline
menu shows database status, accounts, active rentals, listings, and whether
settings are configured without revealing secret values. Only the configured
admin ID is accepted. You can link a FunPay listing to a free account, edit
non-secret account fields (SteamID64, Dota ID, MMR, and manually verified behavior
score), change an existing listing's price, and sync listing text from this menu.
Lot IDs, titles, and initial prices are read from FunPay; only listing title and
description are changed automatically. New MMR values sync daily from OpenDota.
New listings must still be created manually once. Telegram account creation
stores only the Dota ID and optional public listing values; it never asks for
account or email credentials. Telegram long polling
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
