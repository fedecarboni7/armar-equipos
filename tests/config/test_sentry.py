from unittest.mock import patch

import sentry_sdk


def test_sentry_initializes_when_dsn_is_set():
    with patch.dict("os.environ", {"SENTRY_DSN": "https://examplePublicKey@o0.ingest.sentry.io/0", "ENVIRONMENT": "local"}):
        with patch.object(sentry_sdk, "init") as mock_init:
            from app.config.config import create_app
            create_app()
            mock_init.assert_called_once_with(
                dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
                environment="local",
                send_default_pii=True,
                enable_logs=True,
                traces_sample_rate=1.0,
                profile_session_sample_rate=1.0,
                profile_lifecycle="trace",
            )


def test_sentry_does_not_initialize_when_dsn_is_not_set():
    with patch.dict("os.environ", {}, clear=False):
        import os
        os.environ.pop("SENTRY_DSN", None)
        with patch.object(sentry_sdk, "init") as mock_init:
            from app.config.config import create_app
            create_app()
            mock_init.assert_not_called()
