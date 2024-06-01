"""Code for sending emails using AWS SES."""

import json
import boto3
from botocore.exceptions import ClientError
from app.settings import get_settings
import config
from pydantic import BaseModel
from typing import Optional

logger = config.get_logger(__name__)
settings = get_settings()


class FeedbackAvailableData(BaseModel):
    """
    Data for feedback-available email template.
    See terraform/instances/common/email-templates/feedback-available.html
    """

    subject: str  # email subject
    teacher_feedback: str
    other_comments: str
    reflection_score: Optional[str] = None


# see `terraform output` in instances/common/ which should match these values:
FEEDBACK_SES_TEMPLATE = "ezfeedback-common-feedback-available"
SES_CONFIG_SET = "ezfeedback-common-email-failures"


def send_feedback_email(to_email: str, body: FeedbackAvailableData) -> bool:
    ses_client = boto3.client("sesv2", region_name=settings.aws_region)

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sesv2/client/send_email.html
    # TODO: possibly include email of teacher that gave feedback
    reply_to_emails = (
        [settings.support_email] if settings.support_email else [settings.email_from]
    )

    ses_client.send_email(
        FromEmailAddress=settings.email_from,
        Destination={"ToAddresses": [to_email]},
        ReplyToAddresses=reply_to_emails,
        Content={
            "Template": {
                "TemplateName": FEEDBACK_SES_TEMPLATE,
                "TemplateData": body.model_dump_json(),
            }
        },
        ConfigurationSetName=SES_CONFIG_SET,
    )
    # TODO: try catch!
    return True
