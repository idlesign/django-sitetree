from django.apps import AppConfig
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _


class SitetreeConfig(AppConfig):
    """Sitetree configuration."""

    name = 'sitetree'
    verbose_name = _('Site Trees')

    def ready(self):
        cache.delete('sitetrees')
        cache.delete('tree_aliases')
