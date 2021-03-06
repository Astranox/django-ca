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


class HexConverter:  # pragma: only django>=2.1
    regex = '[0-9A-F:]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class Base64Converter:  # pragma: only django>=2.1
    regex = '[a-zA-Z0-9=+/]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
