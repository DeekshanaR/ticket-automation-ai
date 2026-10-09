from app.classifier import get_classifier


def test_category_predictions():
    clf = get_classifier()
    assert clf.predict("VPN not working", "cannot connect to vpn timeout")["category"] == "Network"
    assert clf.predict("Account locked", "forgot password reset needed")["category"] == "Access"
    assert clf.predict("Phishing email", "suspicious link asking credentials")["category"] == "Security"


def test_confidence_range():
    result = get_classifier().predict("Printer offline", "printer stuck in queue")
    assert 0 <= result["confidence"] <= 1
    assert result["priority"] in {"Low", "Medium", "High"}
