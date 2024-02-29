# coding: utf-8

from __future__ import annotations

from datetime import timedelta as td
from unittest.mock import Mock, patch

from django.test.utils import override_settings
from django.utils.timezone import now

from hc.api.models import Channel, Check, Notification
from hc.test import BaseTestCase


class NotifySpikeTestCase(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.check = Check(project=self.project)
        self.check.name = "Foo"
        self.check.status = "down"
        self.check.last_ping = now() - td(minutes=61)
        self.check.save()

        self.channel = Channel(project=self.project)
        self.channel.kind = "spike"
        self.channel.value = "https://spike.example.org"
        self.channel.save()
        self.channel.checks.add(self.check)

    @patch("hc.api.transports.curl.request", autospec=True)
    def test_it_works(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["check_id"], str(self.check.code))
        self.assertEqual(payload["title"], "Foo is DOWN")
        self.assertIn("Foo is DOWN.", payload["message"])
        self.assertIn("Last ping was an hour ago.", payload["message"])

    @override_settings(SPIKE_ENABLED=False)
    def test_it_requires_spike_enabled(self) -> None:
        self.channel.notify(self.check)
        n = Notification.objects.get()
        self.assertEqual(n.error, "Spike notifications are not enabled.")

    @patch("hc.api.transports.curl.request", autospec=True)
    def test_it_does_not_escape(self, mock_post: Mock) -> None:
        self.check.name = "Foo & Bar"
        self.check.status = "up"
        self.check.save()

        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["title"], "Foo & Bar is UP")
        self.assertEqual(payload["message"], "Foo & Bar is UP.")

    @patch("hc.api.transports.curl.request", autospec=True)
    def test_it_handles_no_last_ping(self, mock_post: Mock) -> None:
        self.check.last_ping = None
        self.check.save()
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)

        payload = mock_post.call_args.kwargs["json"]
        self.assertNotIn("Last ping was", payload["message"])
