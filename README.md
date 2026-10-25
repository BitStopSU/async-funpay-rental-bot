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

Если FunPay отклоняет cookie как устаревшую, бот обновляет данные сессии и
повторяет запрос один раз, не чаще раза в минуту. Если ошибка сохраняется,
проверьте `FUNPAY_GOLDEN_KEY` и войдите в FunPay заново, чтобы получить актуальный ключ.

If FunPay rejects a session cookie as stale, the bot refreshes its session data
and retries the request once, at most once per minute. If the error persists,
check `FUNPAY_GOLDEN_KEY` and sign in to FunPay again to obtain a fresh key.
