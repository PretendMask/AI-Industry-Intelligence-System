"""HTML 邮件发送（smtplib + SSL/STARTTLS）。"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from loguru import logger


def _normalize_recipients(recipients: list[str]) -> list[str]:
    normalized: list[str] = []
    for recipient in recipients:
        for part in str(recipient).replace("；", ";").replace(",", ";").split(";"):
            address = part.strip()
            if address:
                normalized.append(address)
    return normalized


def send_html_email(
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    recipients: list[str],
    subject: str,
    html_body: str,
    use_ssl: bool = True,
    timeout: int = 30,
) -> None:
    host = host.strip()
    sender = user.strip()
    recipient_list = _normalize_recipients(recipients)
    if not host:
        raise ValueError("SMTP 主机为空")
    if not recipient_list:
        raise ValueError("邮件收件人为空")
    if not sender:
        raise ValueError("SMTP 账号为空，无法作为发件人发送邮件")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("AI行业情报系统", sender))
    msg["To"] = ", ".join(recipient_list)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    logger.info(
        "准备发送邮件：host={} port={} ssl={} sender={} recipients={}",
        host,
        port,
        use_ssl,
        sender,
        len(recipient_list),
    )

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=timeout) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient_list, msg.as_string())
    else:
        with smtplib.SMTP(host, port, timeout=timeout) as server:
            server.ehlo()
            if server.has_extn("starttls"):
                server.starttls()
                server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, recipient_list, msg.as_string())

    logger.info("邮件发送完成：subject={} recipients={}", subject, len(recipient_list))
