import pytest
from app.notifications import send_feedback_email
from app.settings import get_settings
import app.models as models
from uuid import UUID

settings = get_settings()


@pytest.mark.skip(reason="Requires use of AWS API and is not purely automated.")
def test_send_feedback_email(session):
    """
    Test sending feedback email (note: template may fail to render quietly).
    In the ideal world we'd also mock test the AWS SES API calls but we don't got time for that.
    """

    # TODO: consider that no feedback exists at the start of the test
    # latest_feedback = session.query(models.Feedback).order_by(models.Feedback.created_at.desc()).first()
    feedback_id = UUID("b87bb248-eaf0-486b-b724-607e2c4fc4f0")
    feedback = (
        session.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
    )

    assert feedback
    print(f"sending test email for feedback: {feedback.id}")
    send_feedback_email(feedback)
