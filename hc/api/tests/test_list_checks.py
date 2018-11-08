import json
from datetime import timedelta as td
from django.utils.timezone import now
from django.conf import settings

from hc.api.models import Channel, Check
from hc.test import BaseTestCase


class ListChecksTestCase(BaseTestCase):

    def setUp(self):
        super(ListChecksTestCase, self).setUp()

        self.now = now().replace(microsecond=0)

        self.a1 = Check(user=self.alice, name="Alice 1")
        self.a1.timeout = td(seconds=3600)
        self.a1.grace = td(seconds=900)
        self.a1.last_ping = self.now
        self.a1.n_pings = 1
        self.a1.status = "new"
        self.a1.tags = "a1-tag a1-additional-tag"
        self.a1.save()

        self.a2 = Check(user=self.alice, name="Alice 2")
        self.a2.timeout = td(seconds=86400)
        self.a2.grace = td(seconds=3600)
        self.a2.last_ping = self.now
        self.a2.status = "up"
        self.a2.tags = "a2-tag"
        self.a2.save()

        self.c1 = Channel.objects.create(user=self.alice)
        self.a1.channel_set.add(self.c1)

    def get(self):
        return self.client.get("/api/v1/checks/", HTTP_X_API_KEY="X" * 32)

    def test_it_works(self):
        r = self.get()
        self.assertEqual(r.status_code, 200)

        doc = r.json()
        self.assertEqual(len(doc["checks"]), 2)

        a1 = None
        a2 = None
        for check in doc["checks"]:
            if check["name"] == "Alice 1":
                a1 = check
            if check["name"] == "Alice 2":
                a2 = check

        self.assertEqual(a1["timeout"], 3600)
        self.assertEqual(a1["grace"], 900)
        self.assertEqual(a1["ping_url"], self.a1.url())
        self.assertEqual(a1["last_ping"], self.now.isoformat())
        self.assertEqual(a1["n_pings"], 1)
        self.assertEqual(a1["status"], "new")
        self.assertEqual(a1["channels"], str(self.c1.code))

        update_url = settings.SITE_ROOT + "/api/v1/checks/%s" % self.a1.code
        pause_url = update_url + "/pause"
        self.assertEqual(a1["update_url"], update_url)
        self.assertEqual(a1["pause_url"], pause_url)

        next_ping = self.now + td(seconds=3600)
        self.assertEqual(a1["next_ping"], next_ping.isoformat())

        self.assertEqual(a2["timeout"], 86400)
        self.assertEqual(a2["grace"], 3600)
        self.assertEqual(a2["ping_url"], self.a2.url())
        self.assertEqual(a2["status"], "up")

    def test_it_shows_only_users_checks(self):
        bobs_check = Check(user=self.bob, name="Bob 1")
        bobs_check.save()

        r = self.get()
        data = r.json()
        self.assertEqual(len(data["checks"]), 2)
        for check in data["checks"]:
            self.assertNotEqual(check["name"], "Bob 1")

    def test_it_accepts_api_key_from_request_body(self):
        payload = json.dumps({"api_key": "X" * 32})
        r = self.client.generic("GET", "/api/v1/checks/", payload,
                                content_type="application/json")

        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Alice")

    def test_it_works_with_tags_param(self):
        r = self.client.get("/api/v1/checks/?tag=a2-tag", HTTP_X_API_KEY="X" * 32)
        self.assertEqual(r.status_code, 200)

        doc = r.json()
        self.assertTrue("checks" in doc)
        self.assertEqual(len(doc["checks"]), 1)

        check = doc["checks"][0]

        self.assertEqual(check["name"], "Alice 2")
        self.assertEqual(check["tags"], "a2-tag")

    def test_it_filters_with_multiple_tags_param(self):
        r = self.client.get("/api/v1/checks/?tag=a1-tag&tag=a1-additional-tag", HTTP_X_API_KEY="X" * 32)
        self.assertEqual(r.status_code, 200)

        doc = r.json()
        self.assertTrue("checks" in doc)
        self.assertEqual(len(doc["checks"]), 1)

        check = doc["checks"][0]

        self.assertEqual(check["name"], "Alice 1")
        self.assertEqual(check["tags"], "a1-tag a1-additional-tag")

    def test_it_does_not_match_tag_partially(self):
        r = self.client.get("/api/v1/checks/?tag=tag", HTTP_X_API_KEY="X" * 32)
        self.assertEqual(r.status_code, 200)

        doc = r.json()
        self.assertTrue("checks" in doc)
        self.assertEqual(len(doc["checks"]), 0)

    def test_non_existing_tags_filter_returns_empty_result(self):
        r = self.client.get("/api/v1/checks/?tag=non_existing_tag_with_no_checks", HTTP_X_API_KEY="X" * 32)
        self.assertEqual(r.status_code, 200)

        doc = r.json()
        self.assertTrue("checks" in doc)
        self.assertEqual(len(doc["checks"]), 0)

    def test_readonly_key_works(self):
        self.profile.api_key_readonly = "R" * 32
        self.profile.save()

        r = self.client.get("/api/v1/checks/", HTTP_X_API_KEY="R" * 32)
        self.assertEqual(r.status_code, 200)
