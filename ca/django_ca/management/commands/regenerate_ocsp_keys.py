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

from django.core.management.base import CommandError

from ... import ca_settings
from ...models import CertificateAuthority
from ..base import BaseCommand
from ..base import ExpiresAction


class Command(BaseCommand):
    help = "Regenerate OCSP keys."

    def add_arguments(self, parser):
        parser.add_argument(
            'serial', nargs='*',
            help="Generate OCSP keys only for the given CA. If omitted, generate keys for all CAs.")

        parser.add_argument(
            '--expires', default=2, action=ExpiresAction,
            help='Sign the certificate for DAYS days (default: %(default)s)')

        self.add_algorithm(parser)
        self.add_key_size(parser)
        self.add_key_type(parser)
        self.add_ecc_curve(parser)
        self.add_password(parser)

        self.add_profile(
            parser, 'Override the profile used for generating the certificate. By default, "ocsp" is used.')

    def handle(self, **options):
        serials = options['serial']
        profile = options['profile'] or 'ocsp'

        # Check if the profile exists. Note that this shouldn't really happen, since valid parameters match
        # existing profiles. The only case is when the user undefines the "ocsp" profile, which is the
        # default.
        if profile not in ca_settings.CA_PROFILES:
            raise CommandError('%s: Undefined profile.' % profile)

        if not serials:
            serials = CertificateAuthority.objects.all().order_by('serial').values_list('serial', flat=True)

        for serial in serials:
            try:
                ca = CertificateAuthority.objects.get(serial=serial.replace(':', ''))
            except CertificateAuthority.DoesNotExist:
                self.stderr.write(self.style.ERROR('%s: Unknown CA.' % serial))
                continue

            ca.generate_ocsp_key(
                profile=profile,
                expires=options['expires'],
                algorithm=options['algorithm'],
                key_size=options['key_size'],
                key_type=options['key_type'],
                ecc_curve=options['ecc_curve'],
                password=options['password'],
            )
