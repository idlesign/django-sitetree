from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SitetreeConfig(AppConfig):
    """Sitetree configuration."""

    name = 'sitetree'
    verbose_name = _('Site Trees')
