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
# see <http://www.gnu.org/licenses/>

from io import BytesIO

from freezegun import freeze_time

from cryptography.hazmat.primitives.serialization import Encoding

from django.utils.encoding import force_bytes

from .. import ca_settings
from ..models import Certificate
from ..models import Watcher
from .base import DjangoCAWithCertTestCase
from .base import certs
from .base import timestamps
from .base import override_settings
from .base import override_tmpcadir


@override_settings(CA_MIN_KEY_SIZE=1024, CA_PROFILES={}, CA_DEFAULT_SUBJECT={})
class ViewCertTestCase(DjangoCAWithCertTestCase):
    def _get_format(self, cert):
        return {
            'cn': cert.cn,
            'from': cert.not_before.strftime('%Y-%m-%d %H:%M'),
            'until': cert.not_after.strftime('%Y-%m-%d %H:%M'),
            'pub': cert.pub,
            'md5': cert.get_digest('md5'),
            'sha1': cert.get_digest('sha1'),
            'sha256': cert.get_digest('sha256'),
            'sha512': cert.get_digest('sha512'),
            'subjectKeyIdentifier': cert.subject_key_identifier.as_text(),
            'authorityKeyIdentifier': cert.ca.subject_key_identifier.as_text(),
            'hpkp': cert.hpkp_pin,
            'san': cert.subject_alternative_name,
        }

    def assertBasic(self, status):
        for key, cert in self.basic_certs.items():
            stdout, stderr = self.cmd('view_cert', cert.serial, stdout=BytesIO(), stderr=BytesIO())
            self.assertEqual(stdout.decode('utf-8'), '''Common Name: {cn}
Valid from: {valid_from_short}
Valid until: {valid_until_short}
Status: {status}
SubjectAltName:
    * {subject_alternative_name}
Watchers:
Digest:
    md5: {md5}
    sha1: {sha1}
    sha256: {sha256}
    sha512: {sha512}
HPKP pin: {hpkp}

{pem}'''.format(status=status, **self.get_cert_context(key)))
            self.assertEqual(stderr, b'')

        # test with no pem but with extensions
        for key, cert in self.basic_certs.items():
            stdout, stderr = self.cmd('view_cert', cert.serial, no_pem=True, extensions=True,
                                      stdout=BytesIO(), stderr=BytesIO())
            self.assertEqual(stdout.decode('utf-8'), '''Common Name: {cn}
Valid from: {valid_from_short}
Valid until: {valid_until_short}
Status: {status}
AuthorityInfoAccess{authority_information_access_critical}:
    CA Issuers:
      * URI:{authority_information_access.issuers[0].value}
    OCSP:
      * URI:{authority_information_access.ocsp[0].value}
AuthorityKeyIdentifier{authority_key_identifier_critical}:
    {authority_key_identifier_text}
BasicConstraints (critical):
    CA:FALSE
cRLDistributionPoints:
    * Full Name: URI:{crl}
ExtendedKeyUsage{extended_key_usage_critical}:
    * {extended_key_usage[0]}
    * {extended_key_usage[1]}
KeyUsage{key_usage_critical}:
    * {key_usage[0]}
    * {key_usage[1]}
    * {key_usage[2]}
SubjectAltName{subject_alternative_name_critical}:
    * {subject_alternative_name}
SubjectKeyIdentifier{subject_key_identifier_critical}:
    {subject_key_identifier}
Watchers:
Digest:
    md5: {md5}
    sha1: {sha1}
    sha256: {sha256}
    sha512: {sha512}
HPKP pin: {hpkp}
'''.format(status=status, **self.get_cert_context(key)))
            self.assertEqual(stderr, b'')

    @freeze_time(timestamps['everything_valid'])
    def test_basic(self):
        self.assertBasic(status='Valid')

    @freeze_time(timestamps['before_everything'])
    def test_basic_not_yet_valid(self):
        self.maxDiff = None
        self.assertBasic(status='Not yet valid')

    @freeze_time(timestamps['everything_expired'])
    def test_basic_expired(self):
        self.maxDiff = None
        self.assertBasic(status='Not yet valid')

    @freeze_time("2018-11-10")
    def test_cert_all(self):
        stdout, stderr = self.cmd('view_cert', self.cert_all.serial, no_pem=True, extensions=True,
                                  stdout=BytesIO(), stderr=BytesIO())
        self.assertEqual(stderr, b'')
        self.assertEqual(stdout.decode('utf-8'), '''Common Name: {cn}
Valid from: {from}
Valid until: {until}
Status: {status}
AuthorityInfoAccess{authority_information_access_critical}:
    CA Issuers:
      * URI:{authority_information_access.issuers[0].value}
    OCSP:
      * URI:{authority_information_access.ocsp[0].value}
AuthorityKeyIdentifier{authority_key_identifier_critical}:
    {authority_key_identifier_text}
BasicConstraints{basic_constraints_critical}:
    {basic_constraints_text}
cRLDistributionPoints:
    * {crl_0}
ExtendedKeyUsage{extended_key_usage_critical}:
    * {extended_key_usage[0]}
    * {extended_key_usage[1]}
    * {extended_key_usage[2]}
    * {extended_key_usage[3]}
IssuerAltName{issuer_alternative_name_critical}:
    * {issuer_alternative_name[0]}
KeyUsage{key_usage_critical}:
    * {key_usage[0]}
    * {key_usage[1]}
    * {key_usage[2]}
NameConstraints{name_constraints_critical}:
    Permitted:
      * DNS:{name_constraints.permitted[0].value}
    Excluded:
      * DNS:{name_constraints.excluded[0].value}
OCSPNoCheck (critical): Yes{precert_poison}
SubjectAltName{subject_alternative_name_critical}:
    * {subject_alternative_name[0]}
    * {subject_alternative_name[1]}
SubjectKeyIdentifier{subject_key_identifier_critical}:
    {subject_key_identifier_text}
TLSFeature{tls_feature_critical}:
    * {tls_feature[0]}
    * {tls_feature[1]}{precert_poison_unknown}
Watchers:
Digest:
    md5: {md5}
    sha1: {sha1}
    sha256: {sha256}
    sha512: {sha512}
HPKP pin: {hpkp}
'''.format(**self.get_cert_context('cert_all')))

    @freeze_time("2018-11-10")
    def test_ocsp(self):
        stdout, stderr = self.cmd('view_cert', self.ocsp.serial, no_pem=True, extensions=True,
                                  stdout=BytesIO(), stderr=BytesIO())
        self.assertEqual(stderr, b'')
        self.assertEqual(stdout.decode('utf-8'), '''Common Name: {cn}
Valid from: {from}
Valid until: {until}
Status: {status}
AuthorityInfoAccess{authority_information_access_critical}:
    CA Issuers:
      * URI:{authority_information_access.issuers[0].value}
AuthorityKeyIdentifier{authority_key_identifier_critical}:
    {authority_key_identifier_text}
BasicConstraints{basic_constraints_critical}:
    {basic_constraints_text}
cRLDistributionPoints:
    * {crl_0}
ExtendedKeyUsage{extended_key_usage_critical}:
    * {extended_key_usage[0]}
IssuerAltName{issuer_alternative_name_critical}:
    * {issuer_alternative_name[0]}
KeyUsage{key_usage_critical}:
    * {key_usage[0]}
    * {key_usage[1]}
    * {key_usage[2]}
OCSPNoCheck: Yes
SubjectAltName{subject_alternative_name_critical}:
    * {subject_alternative_name[0]}
SubjectKeyIdentifier{subject_key_identifier_critical}:
    {subject_key_identifier_text}
Watchers:
Digest:
    md5: {md5}
    sha1: {sha1}
    sha256: {sha256}
    sha512: {sha512}
HPKP pin: {hpkp}
'''.format(**self.get_cert_context('ocsp')))

    def test_der(self):
        stdout, stderr = self.cmd('view_cert', self.cert.serial, format=Encoding.DER,
                                  stdout=BytesIO(), stderr=BytesIO())
        expected = '''Common Name: {cn}
Valid from: {from}
Valid until: {until}
Status: {status}
SubjectAltName:
    * {san[0]}
Watchers:
Digest:
    md5: {md5}
    sha1: {sha1}
    sha256: {sha256}
    sha512: {sha512}
HPKP pin: {hpkp}

'''.format(**self.get_cert_context('cert1'))
        expected = force_bytes(expected) + certs['cert1']['der'] + b'\n'

        self.assertEqual(stdout, expected)
        self.assertEqual(stderr, b'')

    def test_revoked(self):
        cert = Certificate.objects.get(serial=self.cert.serial)
        cert.revoked = True
        cert.save()
        stdout, stderr = self.cmd('view_cert', cert.serial, no_pem=True, stdout=BytesIO(), stderr=BytesIO())
        self.assertEqual(stdout.decode('utf-8'), '''Common Name: %(cn)s
Valid from: %(from)s
Valid until: %(until)s
Status: Revoked
SubjectAltName:
    * DNS:%(cn)s
Watchers:
Digest:
    md5: %(md5)s
    sha1: %(sha1)s
    sha256: %(sha256)s
    sha512: %(sha512)s
HPKP pin: %(hpkp)s
''' % certs['cert1'])
        self.assertEqual(stderr, b'')

    @override_tmpcadir()
    def test_no_san_with_watchers(self):
        # test a cert with no subjectAltNames but with watchers.
        cert = self.create_cert(self.ca, self.csr_pem, [('CN', 'example.com')], cn_in_san=False)
        watcher = Watcher.from_addr('user@example.com')
        cert.watchers.add(watcher)

        stdout, stderr = self.cmd('view_cert', cert.serial, no_pem=True, stdout=BytesIO(), stderr=BytesIO())
        self.assertEqual(stdout.decode('utf-8'), '''Common Name: %(cn)s
Valid from: %(from)s
Valid until: %(until)s
Status: Valid
Watchers:
* user@example.com
Digest:
    md5: %(md5)s
    sha1: %(sha1)s
    sha256: %(sha256)s
    sha512: %(sha512)s
HPKP pin: %(hpkp)s
''' % self._get_format(cert))
        self.assertEqual(stderr, b'')

    def test_contrib_multiple_ous_and_no_ext(self):
        stdout, stderr = self.cmd('view_cert', self.cert_multiple_ous_and_no_ext.serial, no_pem=True,
                                  extensions=True, stdout=BytesIO(), stderr=BytesIO())
        self.assertEqual(stderr, b'')
        self.assertEqual(stdout.decode('utf-8'), '''Common Name: %(cn)s
Valid from: 1998-05-18 00:00
Valid until: 2028-08-01 23:59
Status: Valid
Watchers:
Digest:
    md5: A2:33:9B:4C:74:78:73:D4:6C:E7:C1:F3:8D:CB:5C:E9
    sha1: 85:37:1C:A6:E5:50:14:3D:CE:28:03:47:1B:DE:3A:09:E8:F8:77:0F
    sha256: 83:CE:3C:12:29:68:8A:59:3D:48:5F:81:97:3C:0F:91:95:43:1E:DA:37:CC:5E:36:43:0E:79:C7:A8:88:63:8B
    sha512: 86:20:07:9F:8B:06:80:43:44:98:F6:7A:A4:22:DE:7E:2B:33:10:9B:65:72:79:C4:EB:F3:F3:0F:66:C8:6E:89:1D:4C:6C:09:1C:83:45:D1:25:6C:F8:65:EB:9A:B9:50:8F:26:A8:85:AE:3A:E4:8A:58:60:48:65:BB:44:B6:CE
HPKP pin: AjyBzOjnxk+pQtPBUEhwfTXZu1uH9PVExb8bxWQ68vo=
''' % {'cn': ''})  # NOQA

    def test_contrib_cloudflare_1(self):
        stdout, stderr = self.cmd('view_cert', self.cert_cloudflare_1.serial, no_pem=True, extensions=True,
                                  stdout=BytesIO(), stderr=BytesIO())
        self.assertEqual(stderr, b'')

        self.assertEqual(stdout.decode('utf-8'), '''Common Name: {cn}
Valid from: 2018-07-18 00:00
Valid until: 2019-01-24 23:59
Status: Valid
AuthorityInfoAccess:
    CA Issuers:
      * URI:http://crt.comodoca4.com/COMODOECCDomainValidationSecureServerCA2.crt
    OCSP:
      * URI:http://ocsp.comodoca4.com
AuthorityKeyIdentifier:
    keyid:40:09:61:67:F0:BC:83:71:4F:DE:12:08:2C:6F:D4:D4:2B:76:3D:96
BasicConstraints (critical):
    CA:FALSE
cRLDistributionPoints:
    * Full Name: URI:http://crl.comodoca4.com/COMODOECCDomainValidationSecureServerCA2.crl
certificatePolicies:
    * OID 1.3.6.1.4.1.6449.1.2.2.7: https://secure.comodo.com/CPS
    * OID 2.23.140.1.2.1: None
ExtendedKeyUsage:
    * serverAuth
    * clientAuth
KeyUsage (critical):
    * digitalSignature{precert_poison}
SubjectAltName:
    * DNS:sni24142.cloudflaressl.com
    * DNS:*.animereborn.com
    * DNS:*.beglideas.ga
    * DNS:*.chroma.ink
    * DNS:*.chuckscleanings.ga
    * DNS:*.clipvuigiaitris.ga
    * DNS:*.cmvsjns.ga
    * DNS:*.competegraphs.ga
    * DNS:*.consoleprints.ga
    * DNS:*.copybreezes.ga
    * DNS:*.corphreyeds.ga
    * DNS:*.cyanigees.ga
    * DNS:*.dadpbears.ga
    * DNS:*.dahuleworldwides.ga
    * DNS:*.dailyopeningss.ga
    * DNS:*.daleylexs.ga
    * DNS:*.danajweinkles.ga
    * DNS:*.dancewthyogas.ga
    * DNS:*.darkmoosevpss.ga
    * DNS:*.daurat.com.ar
    * DNS:*.deltaberg.com
    * DNS:*.drjahanobgyns.ga
    * DNS:*.drunkgirliess.ga
    * DNS:*.duhiepkys.ga
    * DNS:*.dujuanjsqs.ga
    * DNS:*.dumbiseasys.ga
    * DNS:*.dumpsoftdrinkss.ga
    * DNS:*.dunhavenwoodss.ga
    * DNS:*.durabiliteas.ga
    * DNS:*.duxmangroups.ga
    * DNS:*.dvpdrivewayss.ga
    * DNS:*.dwellwizes.ga
    * DNS:*.dwwkouis.ga
    * DNS:*.entertastic.com
    * DNS:*.estudiogolber.com.ar
    * DNS:*.letsretro.team
    * DNS:*.maccuish.org.uk
    * DNS:*.madamsquiggles.com
    * DNS:*.sftw.ninja
    * DNS:*.spangenberg.io
    * DNS:*.timmutton.com.au
    * DNS:*.wyomingsexbook.com
    * DNS:*.ych.bid
    * DNS:animereborn.com
    * DNS:beglideas.ga
    * DNS:chroma.ink
    * DNS:chuckscleanings.ga
    * DNS:clipvuigiaitris.ga
    * DNS:cmvsjns.ga
    * DNS:competegraphs.ga
    * DNS:consoleprints.ga
    * DNS:copybreezes.ga
    * DNS:corphreyeds.ga
    * DNS:cyanigees.ga
    * DNS:dadpbears.ga
    * DNS:dahuleworldwides.ga
    * DNS:dailyopeningss.ga
    * DNS:daleylexs.ga
    * DNS:danajweinkles.ga
    * DNS:dancewthyogas.ga
    * DNS:darkmoosevpss.ga
    * DNS:daurat.com.ar
    * DNS:deltaberg.com
    * DNS:drjahanobgyns.ga
    * DNS:drunkgirliess.ga
    * DNS:duhiepkys.ga
    * DNS:dujuanjsqs.ga
    * DNS:dumbiseasys.ga
    * DNS:dumpsoftdrinkss.ga
    * DNS:dunhavenwoodss.ga
    * DNS:durabiliteas.ga
    * DNS:duxmangroups.ga
    * DNS:dvpdrivewayss.ga
    * DNS:dwellwizes.ga
    * DNS:dwwkouis.ga
    * DNS:entertastic.com
    * DNS:estudiogolber.com.ar
    * DNS:letsretro.team
    * DNS:maccuish.org.uk
    * DNS:madamsquiggles.com
    * DNS:sftw.ninja
    * DNS:spangenberg.io
    * DNS:timmutton.com.au
    * DNS:wyomingsexbook.com
    * DNS:ych.bid
SubjectKeyIdentifier:
    05:86:D8:B4:ED:A9:7E:23:EE:2E:E7:75:AA:3B:2C:06:08:2A:93:B2{precert_poison_unknown}
Watchers:
Digest:
    md5: {md5}
    sha1: {sha1}
    sha256: {sha256}
    sha512: {sha512}
HPKP pin: {hpkp}
'''.format(**self.get_cert_context('cloudflare_1')))

    def assertContrib(self, cert, expected):
        stdout, stderr = self.cmd('view_cert', cert.serial, no_pem=True, extensions=True,
                                  stdout=BytesIO(), stderr=BytesIO())
        self.assertEqual(stderr, b'')
        self.assertEqual(stdout.decode('utf-8'), expected)

    def test_contrib_godaddy_derstandardat(self):
        self.assertContrib(self.cert_godaddy_derstandardat, '''Common Name: %(cn)s
Valid from: %(valid_from)s
Valid until: %(valid_until)s
Status: Valid
AuthorityInfoAccess:
    CA Issuers:
      * URI:http://certificates.godaddy.com/repository/gdig2.crt
    OCSP:
      * URI:http://ocsp.godaddy.com/
AuthorityKeyIdentifier:
    keyid:40:C2:BD:27:8E:CC:34:83:30:A2:33:D7:FB:6C:B3:F0:B4:2C:80:CE
BasicConstraints (critical):
    CA:FALSE
cRLDistributionPoints:
    * Full Name: URI:http://crl.godaddy.com/gdig2s1-480.crl
certificatePolicies:
    * OID 2.16.840.1.114413.1.7.23.1: http://certificates.godaddy.com/repository/
    * OID 2.23.140.1.2.1: None
ExtendedKeyUsage:
    * serverAuth
    * clientAuth
KeyUsage (critical):
    * digitalSignature
    * keyEncipherment
SubjectAltName:
    * DNS:derstandard.at
    * DNS:www.derstandard.at
    * DNS:live.derstandard.at
    * DNS:cnct02.derstandard.de
    * DNS:immopreise.at
    * DNS:mobil.derstandard.ch
    * DNS:static.derstandard.ch
    * DNS:ds.at
    * DNS:cnct01.derstandard.de
    * DNS:cnct03.derstandard.de
    * DNS:www.dst.de
    * DNS:live.derstandard.de
    * DNS:ipad.derstandard.ch
    * DNS:www.dst.at
    * DNS:cnct01.derstandard.at
    * DNS:mobil.derstandard.at
    * DNS:cnct03.derstandard.at
    * DNS:images.derstandard.at
    * DNS:text.derstandard.at
    * DNS:images.derstandard.ch
    * DNS:static.derstandard.at
    * DNS:cnct03.derstandard.ch
    * DNS:dst.at
    * DNS:www.derstandard.de
    * DNS:derstandard.de
    * DNS:cnct01.derstandard.ch
    * DNS:finden.at
    * DNS:ipad.derstandard.at
    * DNS:cnct02.derstandard.ch
    * DNS:www.finden.at
    * DNS:www.ds.at
    * DNS:static.derstandard.de
    * DNS:mobil.derstandard.de
    * DNS:derstandard.ch
    * DNS:dst.de
    * DNS:www.immopreise.at
    * DNS:www.derstandard.ch
    * DNS:live.derstandard.ch
    * DNS:cnct02.derstandard.at
    * DNS:images.finden.at
    * DNS:images.derstandard.de
    * DNS:secure.derstandard.at
    * DNS:ipad.derstandard.de
SubjectKeyIdentifier:
    36:97:AB:24:CF:50:2B:05:71:B1:4E:0A:4F:18:94:C1:FC:F9:4F:69
Watchers:
Digest:
    md5: %(md5)s
    sha1: %(sha1)s
    sha256: %(sha256)s
    sha512: %(sha512)s
HPKP pin: %(hpkp)s
''' % {
    'cn': 'derstandard.at',
    'valid_from': '2017-04-18 10:04',
    'valid_until': '2019-04-18 10:04',
    'md5': '52:9E:EC:B2:98:A2:62:95:58:1A:3E:ED:44:3C:F1:D4',
    'sha1': '05:0B:C8:D8:93:93:43:1B:46:6F:85:C7:23:20:C8:DE:E4:68:75:D4',
    'sha256': 'B0:DA:1D:FD:A6:73:D0:A0:D1:11:7E:4C:E1:07:AD:12:05:81:03:EB:E1:60:93:40:49:25:F4:95:3F:BF:31:A7',  # NOQA
    'sha512': 'D6:D6:7C:DD:E0:03:21:23:49:43:BD:29:A3:2D:82:BA:32:43:6E:56:D4:68:89:3F:9D:79:29:52:83:B5:91:4E:E2:F6:44:BD:38:C1:29:9B:9E:5F:08:69:BF:E1:91:54:71:24:C6:A5:AD:6A:24:A0:75:FF:95:07:FC:7A:11:B9',  # NOQA
    'hpkp': '0f/TD6A+RCAbsOaPyJUsEzm3BPpoTZ8Btwru1WeSBdw=',
})

    def test_contrib_letsencrypt_jabber_at(self, status='Valid'):
        self.maxDiff = None
        if ca_settings.OPENSSL_SUPPORTS_SCT:
            signedCertificateTimestampList = '''SignedCertificateTimestampList:
    * Precertificate (v1):
        Timestamp: 2018-08-09 10:15:21.724000
        Log ID: 293c519654c83965baaa50fc5807d4b76fbf587a2972dca4c30cf4e54547f478
    * Precertificate (v1):
        Timestamp: 2018-08-09 10:15:21.749000
        Log ID: db74afeecb29ecb1feca3e716d2ce5b9aabb36f7847183c75d9d4f37b61fbf64'''

        else:
            signedCertificateTimestampList = '''SignedCertificateTimestampList:
    Could not parse extension (Requires OpenSSL 1.1.0f or later)'''

        self.assertContrib(self.cert_letsencrypt_jabber_at, '''Common Name: %(cn)s
Valid from: %(valid_from)s
Valid until: %(valid_until)s
Status: %(status)s
AuthorityInfoAccess:
    CA Issuers:
      * URI:http://cert.int-x3.letsencrypt.org/
    OCSP:
      * URI:http://ocsp.int-x3.letsencrypt.org
AuthorityKeyIdentifier:
    keyid:A8:4A:6A:63:04:7D:DD:BA:E6:D1:39:B7:A6:45:65:EF:F3:A8:EC:A1
BasicConstraints (critical):
    CA:FALSE
certificatePolicies:
    * OID 2.23.140.1.2.1: None
    * OID 1.3.6.1.4.1.44947.1.1.1: http://cps.letsencrypt.org, This Certificate may only be relied upon by Relying Parties and only in accordance with the Certificate Policy found at https://letsencrypt.org/repository/
ExtendedKeyUsage:
    * serverAuth
    * clientAuth
KeyUsage (critical):
    * digitalSignature
    * keyEncipherment
%(signedCertificateTimestampList)s
SubjectAltName:
    * DNS:jabber.at
    * DNS:jabber.fsinf.at
    * DNS:jabber.wien
    * DNS:jabber.zone
    * DNS:webchat.jabber.at
    * DNS:www.jabber.at
    * DNS:www.jabber.wien
    * DNS:www.jabber.zone
    * DNS:www.xmpp.zone
    * DNS:xmpp.zone
SubjectKeyIdentifier:
    97:AB:1D:D3:46:04:96:0F:45:DF:C3:FF:59:9D:B0:53:AC:73:79:2E
Watchers:
Digest:
    md5: %(md5)s
    sha1: %(sha1)s
    sha256: %(sha256)s
    sha512: %(sha512)s
HPKP pin: %(hpkp)s
''' % {  # NOQA
    'cn': 'jabber.at',
    'valid_from': '2018-08-09 09:15',
    'valid_until': '2018-11-07 09:15',
    'signedCertificateTimestampList': signedCertificateTimestampList,
    'md5': '90:32:2A:B8:6A:20:5D:A1:20:F3:D5:78:09:30:1F:B2',
    'sha1': 'E9:A5:B4:49:BB:5F:88:51:01:72:D9:B3:CF:E3:8B:F4:A2:C8:E4:08',
    'sha256': 'AF:2D:CE:A3:CE:62:6A:17:E1:CE:BA:7B:A5:A5:F1:A4:3F:0D:80:77:F1:F8:C4:5F:64:27:9A:F9:76:E9:0D:8D',  # NOQA
    'sha512': 'C4:7D:2C:20:DB:C1:63:6D:3B:DC:AA:81:BD:33:18:68:E5:EB:91:0B:C7:85:6A:D6:4F:BB:3E:C0:45:28:FB:8F:6A:5D:86:1B:76:3D:90:A0:64:B3:CB:4E:F3:DC:69:AD:C7:C8:EA:E9:7D:48:1C:B5:D9:43:FE:89:57:32:39:1C',  # NOQA
    'status': status,
    'hpkp': 'rPQ7/P8wLaKwgotVpQfrNo4MRy08pkziFB4Jpd7bnHk=',
})

    @freeze_time("2018-11-10")
    def test_contrib_letsencrypt_jabber_at_expired(self):
        self.test_contrib_letsencrypt_jabber_at('Expired')

    @freeze_time("2017-11-10")  # a year earlier
    def test_contrib_letsencrypt_jabber_at_not_yet_valid(self):
        self.test_contrib_letsencrypt_jabber_at('Not yet valid')

    def test_unknown_cert(self):
        name = 'foobar'
        with self.assertCommandError(r'^Error: %s: Certificate not found\.$' % name):
            self.cmd('view_cert', name, no_pem=True)


@override_settings(CA_MIN_KEY_SIZE=1024, CA_PROFILES={}, CA_DEFAULT_SUBJECT={}, USE_TZ=True)
class ViewCertWithTZTestCase(ViewCertTestCase):
    pass
