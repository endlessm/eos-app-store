import unittest
from mock import Mock

from eos_util.locale_util import LocaleUtil
import os
import locale
from locale import LC_ALL
import sys
import tempfile
import shutil
import datetime

class TestImage(unittest.TestCase):
    def setUp(self):
        os.environ["LC_ALL"] =  "en_US.UTF-8"
        os.environ["LANG"] =  "en_US.UTF-8"
        os.environ["LANGUAGE"] =  "en_US.UTF-8"
        self._dir = tempfile.mkdtemp()
        self._dir_en = os.path.join(self._dir, 'en_US')
        self._dir_pt = os.path.join(self._dir, 'pt_BR')

        os.makedirs(self._dir_en)
        os.makedirs(self._dir_pt)

    def tearDown(self):
        os.environ["LC_ALL"] =  "en_US.UTF-8"
        os.environ["LANG"] =  "en_US.UTF-8"
        os.environ["LANGUAGE"] =  "en_US.UTF-8"
        shutil.rmtree(self._dir)

    def test_get_default_locale_returns_en_us(self):
        self.assertEquals("en_US", LocaleUtil().get_default_locale())

    def test_get_locale_returns_current_locale(self):
        self.assertEquals("en_US", LocaleUtil().get_locale())

    def test_get_locale_returns_current_locale2(self):

        os.environ["LC_ALL"] =  "en_GB.UTF-8"
        os.environ["LANGUAGE"] =  "en_GB.UTF-8"
        os.environ["LANG"] =  "en_GB.UTF-8"

        self.assertEquals("en_GB", LocaleUtil().get_locale())

    def test_append_current_locale_english(self):
        self.assertEquals(self._dir_en, LocaleUtil().append_dir_with_current_locale(self._dir))

    def test_append_current_locale_brazil(self):
        os.environ["LC_ALL"] =  "pt_BR.UTF-8"
        os.environ["LANGUAGE"] =  "pt_BR.UTF-8"
        os.environ["LANG"] =  "pt_BR.UTF-8"
        self.assertEquals(self._dir_pt, LocaleUtil().append_dir_with_current_locale(self._dir))

    def test_append_current_locale_unknown(self):
        os.environ["LC_ALL"] =  "en_GB.UTF-8"
        os.environ["LANGUAGE"] =  "en_GB.UTF-8"
        os.environ["LANG"] =  "en_GB.UTF-8"
        self.assertEquals(self._dir_en, LocaleUtil().append_dir_with_current_locale(self._dir))

    def test_format_date_time_en_us(self):
        timestamp = datetime.datetime(2013, 12, 3, 18, 5, 28, 362319)
        timestring = LocaleUtil().format_date_time(timestamp)
        self.assertEquals(timestring, '06:05 PM')
    
    def test_format_date_time_en_gb(self):
        os.environ["LC_ALL"] =  "en_GB.UTF-8"
        os.environ["LANGUAGE"] =  "en_GB.UTF-8"
        os.environ["LANG"] =  "en_GB.UTF-8"
        locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')
        timestamp = datetime.datetime(2013, 12, 3, 18, 5, 28, 362319)
        timestring = LocaleUtil().format_date_time(timestamp)
        self.assertEquals(timestring, '18:05')

    # I'm commenting out the test for the Brazil locale,
    # in case the build machine does not have the Portuguese language pack installed.
    # For now, since the logic is US vs. anywhere else, the Great Britain test suffices.
    # This test does work on my development machine with the Portuguese support installed.
#    def test_format_date_time_pt_br(self):
#        os.environ["LC_ALL"] =  "pt_BR.UTF-8"
#        os.environ["LANGUAGE"] =  "pt_BR.UTF-8"
#        os.environ["LANG"] =  "pt_BR.UTF-8"
#        locale.setlocale(locale.LC_ALL, '')
#        timestamp = datetime.datetime(2013, 12, 3, 18, 5, 28, 362319)
#        timestring = LocaleUtil().format_date_time(timestamp)
#        self.assertEquals(timestring, '18:05')
