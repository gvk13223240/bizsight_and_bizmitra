from allauth.account.adapter import DefaultAccountAdapter
from core.utils.brevo_email import send_email


class CustomAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        subject = self.render_mail_subject(template_prefix, context)
        html_content = self.render_mail(template_prefix, email, context).body

        send_email(
            subject=subject,
            html_content=html_content,
            to_email=email,
        )

