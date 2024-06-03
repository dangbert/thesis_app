"""Code for sending emails using AWS SES."""

import json
import boto3
from botocore.exceptions import ClientError
from app.settings import get_settings
import config
from pydantic import BaseModel
from typing import Optional
import app.models as models
from app.hardcoded import FeedbackData, MAX_SCORE, RELECTION_SCORE_EXPLANATION

from pydantic import ValidationError

logger = config.get_logger(__name__)
settings = get_settings()


# see `terraform output` in instances/common/ which should match these values:
FEEDBACK_SES_TEMPLATE = "ezfeedback-common-feedback-available"
SES_CONFIG_SET = "ezfeedback-common-email-failures"


# def send_feedback_email(to_email: str, body: FeedbackAvailableData) -> bool:
def send_feedback_email(feedback: models.Feedback) -> bool:
    """
    Notify attempt submitter that feedback is available via email.
    Only call this function for human feedback!
    NOTE: pure jinja email templates rather than the SES specific templates seem more flexible/testable.
    """
    if feedback.is_ai or feedback.user is None:
        logger.error(f"send_feedback_email called for AI feedback: {feedback.id}")
        return False
    ses_client = boto3.client("sesv2", region_name=settings.aws_default_region)

    attempt = feedback.attempt
    assignment = attempt.assignment

    try:
        fdata = FeedbackData(**feedback.data)
    except ValidationError:
        logger.error(f"Feedback data provided in incorrect format: {feedback.id}")
        return False

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sesv2/client/send_email.html
    # TODO: possibly include email of teacher that gave feedback
    reply_to_emails = (
        [settings.support_email]
        if settings.support_email
        else [settings.email_from or ""]
    )

    reviewer_name = feedback.user.name
    APPROVED_MESSAGE = f"Your submission was approved by {reviewer_name}, no further action is currently necessary. Make sure to implement any feedback in your next reflection assignment!"
    RESUBMIT_MESSAGE = f"{reviewer_name} has requested you resubmit this assignment. Follow the instructions mentioned in the feedback."

    approval_msg = APPROVED_MESSAGE if fdata.approved else RESUBMIT_MESSAGE

    other_comments = ""
    if fdata.other_comments:
        other_comments = f"<br /><b>other comments</b>:<br />{fdata.other_comments}"

    reflection_msg = ""
    if fdata.score is not None:
        reflection_msg = f"<br /><b>reflection score</b>: {fdata.score}/{MAX_SCORE}\n{RELECTION_SCORE_EXPLANATION}"

    call_to_action = f"To view the feedback alongside your original submission{' ' if fdata.approved else ' or resubmit your learning goal'} <a class='linkNormalSize' href='{assignment.page_url()}'>click here</a>."

    message = f"""
{approval_msg}
<br />

<b>feedback</b>:
{fdata.feedback}

{other_comments}

{reflection_msg}

{call_to_action}
    """.strip()

    template_data = {
        "subject": f"Feedback available on {assignment.name}{' -- Action Required' if not fdata.approved else ''}",
        "message": message,
        "assignment_name": assignment.name,
        "assignment_url": assignment.page_url(),
        "site_url": settings.site_url,
        "support_email": settings.support_email,
    }

    logger.info(f"Sending feedback email to {attempt.user.email}")
    from_name = (
        "EzFeedback" if settings.is_production else f"EzFeedback ({settings.env})"
    )
    # TODO: try catch!
    ses_client.send_email(
        FromEmailAddress=f"{from_name} <{settings.email_from}>",
        Destination={"ToAddresses": [attempt.user.email]},
        ReplyToAddresses=reply_to_emails,
        Content={
            "Template": {
                "TemplateName": FEEDBACK_SES_TEMPLATE,
                "TemplateData": json.dumps(template_data),
            }
        },
        ConfigurationSetName=SES_CONFIG_SET,
    )
    logger.info(f"Email sent to {attempt.user.email}")
    return True
