"""邮件 Service（开发模式：控制台输出）"""


class EmailService:
    """邮件发送服务"""

    def __init__(self, smtp_config: dict[str, object] | None = None) -> None:
        self.smtp_config = smtp_config

    def send(self, to_email: str, subject: str, body: str) -> bool:
        """发送邮件。开发模式打印到控制台。"""
        print(f"[EMAIL] To: {to_email}")
        print(f"        Subject: {subject}")
        print(f"        Body: {body}")
        return True
