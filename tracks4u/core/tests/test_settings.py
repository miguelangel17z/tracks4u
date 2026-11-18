import importlib
import os
from unittest import mock

from django.test import SimpleTestCase

import tracks4u.settings as project_settings


class SettingsConfigurationTests(SimpleTestCase):
    def test_postgresql_engine_in_databases(self):
        engine = project_settings.DATABASES["default"]["ENGINE"]
        self.assertEqual(engine, "django.db.backends.postgresql")

    def test_db_use_admin_without_admin_user_keeps_default_user(self):
        env_overrides = {
            "DB_USER": "tracks4u_app",
            "DB_PASSWORD": "app_pwd_value",
            "DB_ADMIN_USER": "",
            "DB_ADMIN_PASSWORD": "",
            "DB_USE_ADMIN": "1",
        }
        with mock.patch.dict(os.environ, env_overrides, clear=False):
            reloaded = importlib.reload(project_settings)
            self.assertEqual(reloaded.DATABASES["default"]["USER"], "tracks4u_app")
        importlib.reload(project_settings)

    def test_db_use_admin_with_admin_user_switches_credentials(self):
        env_overrides = {
            "DB_USER": "tracks4u_app",
            "DB_PASSWORD": "app_pwd_value",
            "DB_ADMIN_USER": "tracks4u_admin",
            "DB_ADMIN_PASSWORD": "admin_pwd_value",
            "DB_USE_ADMIN": "1",
        }
        with mock.patch.dict(os.environ, env_overrides, clear=False):
            reloaded = importlib.reload(project_settings)
            self.assertEqual(reloaded.DATABASES["default"]["USER"], "tracks4u_admin")
            self.assertEqual(reloaded.DATABASES["default"]["PASSWORD"], "admin_pwd_value")
        importlib.reload(project_settings)
