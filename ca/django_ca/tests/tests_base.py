"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import tempfile

from django.test import TestCase

from .. import ca_settings
from .base import DjangoCATestCase
from .base import override_settings
from .base import override_tmpcadir


class TestDjangoCATestCase(DjangoCATestCase):
    # test the base test-class

    @override_tmpcadir()
    def test_override_tmpcadir(self):
        ca_dir = ca_settings.CA_DIR
        self.assertTrue(ca_dir.startswith(tempfile.gettempdir()))

    def test_tmpcadir(self):
        old_ca_dir = ca_settings.CA_DIR

        with self.tmpcadir():
            ca_dir = ca_settings.CA_DIR
            self.assertNotEqual(ca_dir, old_ca_dir)
            self.assertTrue(ca_dir.startswith(tempfile.gettempdir()))

        self.assertEqual(ca_settings.CA_DIR, old_ca_dir)  # ensure that they're equal again


class OverrideSettingsFuncTestCase(TestCase):
    @override_settings(CA_MIN_KEY_SIZE=256)
    def test_basic(self):
        self.assertEqual(ca_settings.CA_MIN_KEY_SIZE, 256)


@override_settings(CA_MIN_KEY_SIZE=128)
class OverrideSettingsClassTestCase(DjangoCATestCase):
    def test_basic(self):
        self.assertEqual(ca_settings.CA_MIN_KEY_SIZE, 128)

    @override_settings(CA_MIN_KEY_SIZE=256)
    def test_double(self):
        self.assertEqual(ca_settings.CA_MIN_KEY_SIZE, 256)

    def test_wrong_base(self):
        with self.assertRaises(Exception):
            @override_settings(CA_MIN_KEY_SIZE=256)
            class DummyTest(TestCase):
                pass
