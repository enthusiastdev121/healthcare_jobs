import json

from django.test.utils import override_settings
from hc.api.models import Channel, Check
from hc.test import BaseTestCase


@override_settings(SIGNAL_CLI_ENABLED=True)
class EditSignalTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.check = Check.objects.create(project=self.project)

        self.channel = Channel(project=self.project, kind="signal")
        self.channel.value = json.dumps(
            {"value": "+12345678", "up": True, "down": True}
        )
        self.channel.save()

        self.url = f"/integrations/{self.channel.code}/edit/"

    def test_instructions_work(self):
        self.client.login(username="alice@example.org", password="password")
        r = self.client.get(self.url)
        self.assertContains(r, "Signal Settings")
        self.assertContains(r, "Get a Signal message")
        self.assertContains(r, "+12345678")

    def test_it_updates_channel(self):
        form = {
            "label": "My Phone",
            "phone": "+1234567890",
            "down": "true",
            "up": "false",
        }

        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(self.url, form)
        self.assertRedirects(r, self.channels_url)

        self.channel.refresh_from_db()
        self.assertEqual(self.channel.phone_number, "+1234567890")
        self.assertEqual(self.channel.name, "My Phone")
        self.assertTrue(self.channel.signal_notify_down)
        self.assertFalse(self.channel.signal_notify_up)

        # Make sure it does not call assign_all_checks
        self.assertFalse(self.channel.checks.exists())

    def test_it_obeys_up_down_flags(self):
        form = {"label": "My Phone", "phone": "+1234567890"}

        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(self.url, form)
        self.assertRedirects(r, self.channels_url)

        self.channel.refresh_from_db()
        self.assertFalse(self.channel.signal_notify_down)
        self.assertFalse(self.channel.signal_notify_up)

    @override_settings(SIGNAL_CLI_ENABLED=False)
    def test_it_handles_disabled_integration(self):
        self.client.login(username="alice@example.org", password="password")
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 404)

    def test_it_requires_rw_access(self):
        self.bobs_membership.role = "r"
        self.bobs_membership.save()

        self.client.login(username="bob@example.org", password="password")
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 403)
