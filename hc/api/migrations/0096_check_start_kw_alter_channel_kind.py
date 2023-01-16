# Generated by Django 4.1.4 on 2023-01-16 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0095_check_last_start_rid"),
    ]

    operations = [
        migrations.AddField(
            model_name="check",
            name="start_kw",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="channel",
            name="kind",
            field=models.CharField(
                choices=[
                    ("apprise", "Apprise"),
                    ("call", "Phone Call"),
                    ("discord", "Discord"),
                    ("email", "Email"),
                    ("gotify", "Gotify"),
                    ("hipchat", "HipChat"),
                    ("linenotify", "LINE Notify"),
                    ("matrix", "Matrix"),
                    ("mattermost", "Mattermost"),
                    ("msteams", "Microsoft Teams"),
                    ("ntfy", "ntfy"),
                    ("opsgenie", "Opsgenie"),
                    ("pagerteam", "Pager Team"),
                    ("pagertree", "PagerTree"),
                    ("pd", "PagerDuty"),
                    ("po", "Pushover"),
                    ("pushbullet", "Pushbullet"),
                    ("shell", "Shell Command"),
                    ("signal", "Signal"),
                    ("slack", "Slack"),
                    ("sms", "SMS"),
                    ("spike", "Spike"),
                    ("telegram", "Telegram"),
                    ("trello", "Trello"),
                    ("victorops", "Splunk On-Call"),
                    ("webhook", "Webhook"),
                    ("whatsapp", "WhatsApp"),
                    ("zendesk", "Zendesk"),
                    ("zulip", "Zulip"),
                ],
                max_length=20,
            ),
        ),
    ]
