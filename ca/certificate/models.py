# -*- coding: utf-8 -*-
#
# This file is part of fsinf-certificate-authority
# (https://github.com/fsinf/certificate-authority).
#
# fsinf-certificate-authority is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# fsinf-certificate-authority is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# fsinf-certificate-authority.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

from OpenSSL import crypto

from certificate.managers import CertificateManager


class Certificate(models.Model):
    _x509 = None

    objects = CertificateManager()

    watchers = models.ManyToManyField(User)

    created = models.DateTimeField(auto_now=True)
    expires = models.DateTimeField(null=False, blank=False)

    csr = models.TextField(null=False, blank=False)
    pub = models.TextField(null=False, blank=False)

    cn = models.CharField(max_length=64, null=False, blank=False)
    serial = models.CharField(max_length=35, null=False, blank=False)
    revoked = models.BooleanField(default=False)
    revoked_reason = models.CharField(max_length=32, null=False, blank=False, default='unspecified')

    def save(self, *args, **kwargs):
        if self.pk is None or self.serial is None:
            self.serial = hex(self.x509.get_serial_number())
        super(Certificate, self).save(*args, **kwargs)

    @property
    def x509(self):
        if self._x509 is None:
            self._x509 = crypto.load_certificate(crypto.FILETYPE_PEM, self.pub)
        return self._x509

    def get_revocation(self):
        """Get a crypto.Revoked object or None if the cert is not revoked."""

        if self.revoked:
            r = crypto.Revoked()
            r.set_serial(self.serial)
            r.set_reason(self.revoked_reason)
            return r
