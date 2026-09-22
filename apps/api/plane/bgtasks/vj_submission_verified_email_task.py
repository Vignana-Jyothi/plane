# Python imports
import logging

# Third party imports
from celery import shared_task
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string

# Module imports
from plane.license.utils.instance_value import get_email_configuration
from plane.utils.email import generate_plain_text_from_html
from plane.utils.exception_logger import log_exception


@shared_task
def vj_submission_verified_email(submission_type, title, added_by_name, added_by_email, submission_url):
    """
    Notifies a student when their public-site Problem or Idea submission is
    approved by Talent Wing - the "Submitter is notified via signal webhook"
    line in the SOP (a Django signal + this task, not the Signal messaging
    app - see the digression in an earlier chat about that exact wording).
    Fired from the admin proxy's verify endpoints, since Django never gets
    its own post_save signal for a Problem/Idea (they're Prisma-owned rows -
    see the header comment in backend/prisma/schema.prisma).
    """
    try:
        context = {
            "submission_type": submission_type,
            "title": title,
            "addedByName": added_by_name or "there",
            "email": added_by_email,
            "submission_url": submission_url,
        }

        (
            EMAIL_HOST,
            EMAIL_HOST_USER,
            EMAIL_HOST_PASSWORD,
            EMAIL_PORT,
            EMAIL_USE_TLS,
            EMAIL_USE_SSL,
            EMAIL_FROM,
        ) = get_email_configuration()

        subject = f'Your {submission_type} "{title}" was approved'

        html_content = render_to_string("emails/notifications/vj_submission_verified.html", context)
        text_content = generate_plain_text_from_html(html_content)

        connection = get_connection(
            host=EMAIL_HOST,
            port=int(EMAIL_PORT),
            username=EMAIL_HOST_USER,
            password=EMAIL_HOST_PASSWORD,
            use_tls=EMAIL_USE_TLS == "1",
            use_ssl=EMAIL_USE_SSL == "1",
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=EMAIL_FROM,
            to=[added_by_email],
            connection=connection,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logging.getLogger("plane.worker").info("VJ submission-verified email sent successfully.")
        return
    except Exception as e:
        log_exception(e)
        return
