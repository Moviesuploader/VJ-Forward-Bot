# VJ Forward Bot

Advanced Telegram forwarding bot with public Bot API forwarding and optional user-account forwarding through a user session.

## Features

- Public channel forwarding with a bot or user session
- Custom captions and inline URL buttons
- Skip duplicate documents
- Skip by file extension, filename keywords, and minimum/maximum file size
- Filter message types
- Resume saved forwarding jobs after a worker restart
- Multiple destination channels and per-user settings
- Admin broadcast and status commands

## One-click Heroku deployment

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy?template=https://github.com/Moviesuploader/VJ-Forward-Bot)

The app runs as a **worker dyno** because it uses a Telegram polling client and does not need an inbound web server. Heroku worker dynos are paid; the manifest requests one Basic worker dyno. Review current Heroku pricing before confirming deployment.

The Deploy button asks for these config vars:

| Config var | Description |
|---|---|
| `API_ID` | Telegram API ID from https://my.telegram.org |
| `API_HASH` | Telegram API hash from https://my.telegram.org |
| `BOT_TOKEN` | Main bot token from @BotFather |
| `BOT_OWNER` | Your numeric Telegram user ID |
| `DATABASE_URI` | MongoDB Atlas connection URI (network access must allow Heroku) |
| `DATABASE_NAME` | Optional database name; defaults to `vj-forward-bot` |

Keep all credentials in Heroku Config Vars. Never commit tokens, API hashes, MongoDB URIs, or user session strings to GitHub.

## Manual Heroku deployment

1. Fork this repository or use the Deploy button above.
2. Enter the required config vars during setup.
3. Complete deployment, then open **Heroku Dashboard → Resources** and confirm `worker` is enabled.
4. Open **More → View logs**. A successful startup should show MongoDB verification and the Telegram bot username.
5. Send `/start` to the bot, configure a forwarding bot/user session and destination channel with `/settings`, then run `/forward`.

## Local run

Use Python 3.12, install `requirements.txt`, set the same environment variables, and run:

```bash
python -m pip install -r requirements.txt
python -u main.py
```

## Important notes

- MongoDB Atlas must allow connections from the Heroku app (or use an appropriate network access policy).
- Telegram user-session forwarding is optional and carries account restrictions/risks; use only accounts and chats you are authorized to access.
- Telegram flood limits still apply. Large jobs may take time and can be paused by Telegram flood waits.
- This project uses Pyrofork (MTProto). Telegram Bot API HTTP-only features are not automatically available through Pyrofork unless its MTProto/client layer implements the corresponding operation.

## Credits

Original project and bot concept by [Tech VJ](https://youtube.com/@Tech_VJ). Please retain the original credits and license.
