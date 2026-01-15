"""
Notification system for AutoSpendTracker.

This module provides a centralized notification system using Apprise library,
supporting multiple notification channels including email, webhooks, and more.
"""

import logging
import os
import traceback
from urllib.parse import urlsplit
from datetime import datetime
from typing import Any, Optional

try:
    from apprise import Apprise, NotifyType
except ImportError:
    # Graceful degradation if Apprise is not installed
    Apprise = None  # type: ignore
    NotifyType = None  # type: ignore

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Raised when notification fails."""

    pass


def _redact_webhook(webhook: str) -> str:
    try:
        parts = urlsplit(webhook)
        if not parts.scheme or not parts.netloc:
            return "<redacted>"
        return f"{parts.scheme}://{parts.netloc}/..."
    except Exception:
        return "<redacted>"


def is_notifications_enabled() -> bool:
    """Check if notifications are enabled via environment variable."""
    return os.getenv("NOTIFICATION_ENABLED", "false").lower() == "true"


def configure_apprise() -> Optional[Apprise]:
    """
    Configure Apprise with notification services from environment variables.

    Returns:
        Configured Apprise instance, or None if not available/configured.

    Environment Variables:
        NOTIFICATION_EMAIL: Recipient email address
        NOTIFICATION_SMTP_HOST: SMTP server hostname
        NOTIFICATION_SMTP_PORT: SMTP server port
        NOTIFICATION_SMTP_USER: SMTP username
        NOTIFICATION_SMTP_PASSWORD: SMTP password
        NOTIFICATION_WEBHOOK: Optional webhook URL
    """
    if Apprise is None:
        logger.warning("Apprise library not available, notifications disabled")
        return None

    if not is_notifications_enabled():
        logger.info("Notifications disabled via NOTIFICATION_ENABLED=false")
        return None

    apobj = Apprise()
    services_added = 0

    # Configure Email (SMTP)
    email = os.getenv("NOTIFICATION_EMAIL")
    smtp_host = os.getenv("NOTIFICATION_SMTP_HOST")
    smtp_port = os.getenv("NOTIFICATION_SMTP_PORT", "587")
    smtp_user = os.getenv("NOTIFICATION_SMTP_USER")
    smtp_pass = os.getenv("NOTIFICATION_SMTP_PASSWORD")

    if email and smtp_host and smtp_user and smtp_pass:
        # Build mailto URL for Apprise
        # Format: mailtos://user:password@domain:port?to=recipient
        mailto_url = (
            f"mailtos://{smtp_user}:{smtp_pass}@{smtp_host}:{smtp_port}"
            f"?to={email}&from={smtp_user}"
        )
        apobj.add(mailto_url)
        services_added += 1
        logger.info(f"Email notifications configured: {email}")
    else:
        logger.warning(
            "Email notification not configured. Missing environment variables: "
            "NOTIFICATION_EMAIL, NOTIFICATION_SMTP_HOST, NOTIFICATION_SMTP_USER, "
            "NOTIFICATION_SMTP_PASSWORD"
        )

    # Configure Webhook (optional)
    webhook = os.getenv("NOTIFICATION_WEBHOOK")
    if webhook:
        apobj.add(webhook)
        services_added += 1
        logger.info(f"Webhook notification configured: {_redact_webhook(webhook)}")

    if services_added == 0:
        logger.warning("No notification services configured")
        return None

    logger.info(f"Notification system configured with {services_added} service(s)")
    return apobj


def send_success_notification(
    email_count: int,
    transaction_count: int,
    total_amount: float,
    runtime: float,
    api_cost: float = 0.0,
) -> bool:
    """
    Send success notification with pipeline metrics.

    Args:
        email_count: Number of emails processed
        transaction_count: Number of transactions extracted
        total_amount: Total transaction amount
        runtime: Pipeline execution time in seconds
        api_cost: Estimated API cost in dollars

    Returns:
        True if notification sent successfully, False otherwise
    """
    # Check if success notifications are enabled
    if not os.getenv("NOTIFICATION_ON_SUCCESS", "true").lower() == "true":
        logger.debug("Success notifications disabled")
        return False

    apobj = configure_apprise()
    if apobj is None:
        logger.debug("Notifications not configured, skipping success notification")
        return False

    try:
        # Build notification content
        today = datetime.now().strftime("%Y-%m-%d")
        title = f"✅ AutoSpendTracker - Daily Run Successful"

        body = f"""
📊 Daily Report - {today}

✅ Status: Success
📧 Emails Processed: {email_count}
💰 Total Amount: ${total_amount:.2f}
📝 Transactions Saved: {transaction_count}
⏱️  Runtime: {runtime:.1f} seconds
💵 API Cost: ${api_cost:.4f}

🎉 All transactions have been successfully processed and saved to Google Sheets!

---
AutoSpendTracker - Automated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """.strip()

        # Send notification
        if NotifyType:
            success = apobj.notify(title=title, body=body, notify_type=NotifyType.SUCCESS)
        else:
            success = apobj.notify(title=title, body=body)

        if success:
            logger.info("Success notification sent")
            return True
        else:
            logger.warning("Failed to send success notification")
            return False

    except Exception as e:
        logger.error(f"Error sending success notification: {e}", exc_info=True)
        return False


def send_failure_notification(
    error: Exception,
    context: Optional[dict[str, Any]] = None,
) -> bool:
    """
    Send failure notification with error details.

    Args:
        error: The exception that caused the failure
        context: Optional dictionary with additional context
                (e.g., runtime, last_successful_run)

    Returns:
        True if notification sent successfully, False otherwise
    """
    # Failure notifications are always sent if configured
    apobj = configure_apprise()
    if apobj is None:
        logger.debug("Notifications not configured, skipping failure notification")
        return False

    try:
        # Build notification content
        today = datetime.now().strftime("%Y-%m-%d")
        title = f"❌ AutoSpendTracker - Daily Run Failed"

        # Get error details
        error_type = type(error).__name__
        error_message = str(error)

        # Get truncated stack trace (last 10 lines)
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        tb_summary = "".join(tb_lines[-10:])  # Last 10 lines

        body = f"""
⚠️  Error Report - {today}

❌ Status: Failed
🔴 Error Type: {error_type}
📝 Message: {error_message}

📋 Stack Trace (last 10 lines):
{tb_summary}

🔍 Troubleshooting:
1. Check container logs: docker logs autospendtracker-app
2. Verify credentials are valid
3. Check Google API quotas
4. Review recent code changes

---
AutoSpendTracker - Failed on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """.strip()

        # Add context if provided
        if context:
            context_str = "\n".join(
                f"  {key}: {value}" for key, value in context.items()
            )
            body += f"\n\n📊 Additional Context:\n{context_str}"

        # Send notification
        if NotifyType:
            success = apobj.notify(title=title, body=body, notify_type=NotifyType.FAILURE)
        else:
            success = apobj.notify(title=title, body=body)

        if success:
            logger.info("Failure notification sent")
            return True
        else:
            logger.warning("Failed to send failure notification")
            return False

    except Exception as e:
        logger.error(f"Error sending failure notification: {e}", exc_info=True)
        return False


def send_warning_notification(
    warning_message: str,
    details: Optional[dict[str, Any]] = None,
) -> bool:
    """
    Send warning notification for non-critical issues.

    Args:
        warning_message: The warning message
        details: Optional dictionary with additional details

    Returns:
        True if notification sent successfully, False otherwise
    """
    apobj = configure_apprise()
    if apobj is None:
        logger.debug("Notifications not configured, skipping warning notification")
        return False

    try:
        # Build notification content
        today = datetime.now().strftime("%Y-%m-%d")
        title = f"⚠️  AutoSpendTracker - Warning"

        body = f"""
⚠️  Warning Report - {today}

📝 Message: {warning_message}
        """.strip()

        # Add details if provided
        if details:
            details_str = "\n".join(
                f"  {key}: {value}" for key, value in details.items()
            )
            body += f"\n\n📊 Details:\n{details_str}"

        body += f"\n\n---\nAutoSpendTracker - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Send notification
        if NotifyType:
            success = apobj.notify(title=title, body=body, notify_type=NotifyType.WARNING)
        else:
            success = apobj.notify(title=title, body=body)

        if success:
            logger.info("Warning notification sent")
            return True
        else:
            logger.warning("Failed to send warning notification")
            return False

    except Exception as e:
        logger.error(f"Error sending warning notification: {e}", exc_info=True)
        return False


def test_notification() -> bool:
    """
    Send a test notification to verify configuration.

    Returns:
        True if test notification sent successfully, False otherwise
    """
    apobj = configure_apprise()
    if apobj is None:
        print("❌ Notifications not configured")
        print("\nRequired environment variables:")
        print("  - NOTIFICATION_ENABLED=true")
        print("  - NOTIFICATION_EMAIL=your@email.com")
        print("  - NOTIFICATION_SMTP_HOST=smtp.gmail.com")
        print("  - NOTIFICATION_SMTP_PORT=587")
        print("  - NOTIFICATION_SMTP_USER=your@gmail.com")
        print("  - NOTIFICATION_SMTP_PASSWORD=your-app-password")
        return False

    try:
        title = "🧪 AutoSpendTracker - Test Notification"
        body = f"""
This is a test notification from AutoSpendTracker.

If you're receiving this, your notification system is configured correctly! ✅

Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """.strip()

        if NotifyType:
            success = apobj.notify(title=title, body=body, notify_type=NotifyType.INFO)
        else:
            success = apobj.notify(title=title, body=body)

        if success:
            print("✅ Test notification sent successfully!")
            print("   Check your email/webhook to confirm receipt.")
            return True
        else:
            print("❌ Failed to send test notification")
            print("   Check your SMTP credentials and settings")
            return False

    except Exception as e:
        print(f"❌ Error sending test notification: {e}")
        traceback.print_exc()
        return False


# CLI for testing notifications
if __name__ == "__main__":
    import sys

    print("AutoSpendTracker Notification Test")
    print("=" * 50)
    print()

    # Load .env file if present
    try:
        from dotenv import load_dotenv

        load_dotenv()
        print("✓ Loaded .env file")
    except ImportError:
        print("⚠ python-dotenv not available, using existing environment")

    print()

    # Test notification
    if test_notification():
        sys.exit(0)
    else:
        sys.exit(1)
