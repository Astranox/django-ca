# -*- coding: utf-8 -*-
#
# This file is part of django-ca (https://github.com/mathiasertl/django-ca).
#
# django-ca is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# django-ca is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with django-ca.  If not,
# see <http://www.gnu.org/licenses/>.

from ..base import BaseCommand
from ...models import CertificateAuthority


class Command(BaseCommand):
    help = 'List available certificate authorities.'

    def handle(self, **options):
        for ca in CertificateAuthority.objects.all():
            text = '%s - %s' % (ca.serial, ca.name)
            if ca.enabled is False:
                text += ' (disabled)'

            self.stdout.write(text)
