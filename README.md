## Telegram app monetize report bot

This is a simple Telegram bot that can fetch data from ad networks and send it as messages to a Telegram chat

#### Supported ad networks

* [Appodeal](https://appodeal.ru/)

#### Chat commands

* /report_day — requests stats for current day
* /report_month — requests stats from first day of current month to the current day

#### Command line

* token — Telegram bot token
* ad-api — Appodeal API key
* ad-uid — Appodeal user ID

#### Usage example

```
python monetize_report_bot.py --token 1234567890:AAaAaaAaAAAaA_BbbBBbBbbbBB-CCCccCcc --ad-api DDDDddD1dd2DDd3dDD56d7ddd8ddDd --ad-uid 123456
```

#### License

Feel free to use for any purpose. Distributed under the WTFPL License.
