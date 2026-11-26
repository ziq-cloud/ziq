import datetime as dt

import post_quote as pq


def test_quotes_load_and_skip_comments():
    quotes = pq.load_quotes()
    assert len(quotes) >= 30
    assert not any(q.startswith("#") for q in quotes)


def test_consecutive_days_get_different_quotes():
    quotes = pq.load_quotes()
    d = dt.date(2026, 11, 27)
    assert pq.pick_quote(quotes, d) != pq.pick_quote(quotes, d + dt.timedelta(days=1))


def test_message_has_malay_date_and_escapes_html():
    msg = pq.build_message("Risk < 2% & sabar", dt.date(2026, 11, 27))
    assert "Jumaat, 27 November 2026" in msg
    assert "Risk &lt; 2% &amp; sabar" in msg


def test_missing_env_returns_error(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    assert pq.main([]) == 1
