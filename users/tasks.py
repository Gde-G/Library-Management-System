from celery import shared_task

from django.template.loader import get_template
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from .models import User
from .tokens import account_activation_token


@shared_task
def send_email(request_domain, request_secure, username, to_email, mail_subject: str, template: str, token=None):
    try:

        user = User.objects.get(username=username)
        mail_subject = mail_subject

        context = {
            'user': user.username,
            'domain': request_domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': token if token else account_activation_token.make_token(user),
            'protocol': 'https' if request_secure else 'http',
        }

        temp = get_template(template)

        content = temp.render(context)

        corr = EmailMultiAlternatives(
            subject=mail_subject,
            from_email=settings.EMAIL_HOST_USER,
            to=[to_email],
        )

        corr.attach_alternative(content, 'text/html')
        corr.send(fail_silently=False)

        return "Task Completed Successfully."

    except Exception as e:
        return f"Task Fail Send mail to {username}: {str(e)}."
