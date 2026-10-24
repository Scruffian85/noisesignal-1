from email_notifier import EmailNotifier


def test_weekly_summary_escapes_track_text():
    tracks = [{"title": "<script>x</script>", "artist": "A & B", "country": "IS", "views": 1000, "final_score": 1.0}]
    out = EmailNotifier()._generate_weekly_summary_html(tracks, "https://example.com/?a=1&b=2", "now")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert "A &amp; B" in out


def test_error_alert_escapes_message():
    out = EmailNotifier()._generate_error_alert_html("Boom", "<b>bad</b>", "now")
    assert "<b>bad</b>" not in out
    assert "&lt;b&gt;bad&lt;/b&gt;" in out


def test_send_email_failure_returns_false(monkeypatch):
    import smtplib

    def boom(*a, **kw):
        raise OSError("no network")

    monkeypatch.setattr(smtplib, "SMTP", boom)
    assert EmailNotifier().send_email("s", "<p>x</p>") is False
