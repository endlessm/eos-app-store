import unittest

from application_store.recommended_sites_provider import RecommendedSitesProvider
import os
import shutil
import tempfile
from mock import Mock, patch
from desktop_files.link_model import LinkModel

class RecommendedSitesProviderTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp_directory = tempfile.mkdtemp()
        self._tmp_directory_en = os.path.join(self._tmp_directory, 'en_US')
        self._tmp_directory_pt = os.path.join(self._tmp_directory, 'pt_BR')

        os.makedirs(self._tmp_directory_en)
        os.makedirs(self._tmp_directory_pt)

        self._make_file(self._tmp_directory_en, 'link1.desktop', '[Desktop Entry]\nCategories=Network\nType=Link\nName=link1\nURL=foo1\nComment=comment1')
        self._make_file(self._tmp_directory_en, 'link2.desktop', '[Desktop Entry]\nCategories=Network\nType=Link\nName=link2\nURL=foo2\nComment=comment2')
        self._make_file(self._tmp_directory_en, 'link3.desktop', '[Desktop Entry]\nCategories=Network\nType=Link\nName=link3\nURL=foo3\nComment=comment3')

        self._make_file(self._tmp_directory_pt, 'link4.desktop', '[Desktop Entry]\nCategories=Network\nType=Link\nName=link4\nURL=foo4\nComment=comment4')
        self._make_file(self._tmp_directory_pt, 'link5.desktop', '[Desktop Entry]\nCategories=Network\nType=Link\nName=link5\nURL=foo5\nComment=comment5')

        self._mock_locale_util = Mock()
        self._mock_locale_util.append_dir_with_current_locale = Mock(return_value=self._tmp_directory_en)

    def tearDown(self):
        try:
            shutil.rmtree(self._tmp_directory, True)
        except:
            pass
        
    def test_links_are_sorted_by_name(self):
        self._make_file(self._tmp_directory_pt, 'zed.desktop', '[Desktop Entry]\nCategories=API\nType=Link\nName=aardvark\nURL=bash\nComment=zeta')
        self._mock_locale_util.append_dir_with_current_locale = Mock(return_value=self._tmp_directory_pt)
        self._test_object = RecommendedSitesProvider(self._tmp_directory, locale_util=self._mock_locale_util)
        sites = self._test_object.get_recommended_sites()

        self.assertEquals(3, len(sites))
        
        self.assertEqual(sites[0].name(), 'aardvark')
        self.assertEqual(sites[1].name(), 'link4')
        self.assertEqual(sites[2].name(), 'link5')

    def test_when_retrieving_english_sites_you_are_given_links_in_localized_folder(self):
        self._mock_locale_util.append_dir_with_current_locale = Mock(return_value=self._tmp_directory_en)
        self._test_object = RecommendedSitesProvider(self._tmp_directory, locale_util=self._mock_locale_util)
        sites = self._test_object.get_recommended_sites()

        self.assertEquals(3, len(sites))
        expected_links = {'foo1': LinkModel('', 'link1', 'foo1', 'comment1'),
                          'foo2': LinkModel('', 'link2', 'foo2', 'comment2'),
                          'foo3': LinkModel('', 'link3', 'foo3', 'comment3')}

        self.assertLinkEquals(expected_links.get(sites[0].url()), sites[0])
        self.assertLinkEquals(expected_links.get(sites[1].url()), sites[1])
        self.assertLinkEquals(expected_links.get(sites[2].url()), sites[2])

    def test_when_retrieving_portuguese_sites_you_are_given_links_in_localized_folder(self):
        self._mock_locale_util.append_dir_with_current_locale = Mock(return_value=self._tmp_directory_pt)
        self._test_object = RecommendedSitesProvider(self._tmp_directory, locale_util=self._mock_locale_util)
        sites = self._test_object.get_recommended_sites()

        self.assertEquals(2, len(sites))
        expected_links = {'foo4': LinkModel('', 'link4', 'foo4', 'comment4'),
                          'foo5': LinkModel('', 'link5', 'foo5', 'comment5')}

        self.assertLinkEquals(expected_links.get(sites[0].url()), sites[0])
        self.assertLinkEquals(expected_links.get(sites[1].url()), sites[1])

    def assertLinkEquals(self, link1, link2):
        self.assertEquals(link1.name(), link2.name())
        self.assertEquals(link1.url(), link2.url())
        self.assertEquals(link1.comment(), link2.comment())

    def _make_file(self, dirname, filename, content):
        with open(os.path.join(dirname, filename), 'w') as f:
            f.write(content)
