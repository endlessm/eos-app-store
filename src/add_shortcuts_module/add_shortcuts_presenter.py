import os
import urllib2
from eos_util import image_util
import sys
import gettext

from add_shortcuts_model import AddShortcutsModel
from osapps.app_shortcut import AppShortcut
from osapps.desktop_locale_datastore import DesktopLocaleDatastore
from application_store.application_store_model import ApplicationStoreModel
from shortcut_category import ShortcutCategory
from desktop_files.link_model import LinkModel
from application_store.recommended_sites_provider import RecommendedSitesProvider
from add_shortcuts_module.name_format_util import NameFormatUtil

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class AddShortcutsPresenter():
    IMAGE_CACHE_PATH = '/tmp/'  #maybe /tmp/endless-image-cache/ ?
    
    def __init__(self, url_opener = urllib2.urlopen, pixbuf_loader = image_util.load_pixbuf, view=None):
        self._model = AddShortcutsModel()
        self._url_opener = url_opener
        self._pixbuf_loader = pixbuf_loader
        self._app_desktop_datastore = DesktopLocaleDatastore()
        self._app_store_model = ApplicationStoreModel()
        self._add_shortcuts_view = view
        self._sites_provider = RecommendedSitesProvider()
        self._name_format_util = NameFormatUtil()

    def get_category_data(self):
        category_data = self._model.get_category_data()
        app_categories = self._app_store_model.get_categories()
        for category in category_data:
            if category.category == _('APP') and app_categories:
                for app_category in app_categories:
                    category.subcategories.append(ShortcutCategory(app_category.name()))
                category.subcategories[0].active = True
        return category_data


    def create_directory(self, dir_name, image_file):
        shortcuts = self._app_desktop_datastore.get_all_shortcuts()
        dir_name = self.check_dir_name(dir_name, shortcuts)
        path = self._model.create_directory(dir_name)
        if path:
            # Hack to get hover and down states for Endless folder icons
            if image_file.endswith('_normal.png'):
                icon_dict = {'normal':image_file,
                             'mouseover':image_file.replace('_normal.png', '_hover.png'),
                             'pressed':image_file.replace('_normal.png', '_down.png')}
            else:
                icon_dict = {'normal':image_file}
            shortcut = AppShortcut(key='', name=dir_name, icon=icon_dict)
            self._app_desktop_datastore.add_shortcut(shortcut)
        self._add_shortcuts_view.close()
            
    def add_shortcut(self, shortcut):
        #self._app_desktop_datastore.add_shortcut(shortcut)
        self._add_shortcuts_view.close()

    def get_folder_icons(self, path, prefix='', suffix=''):
        return self._model.get_folder_icons(path, prefix, suffix)

    def check_dir_name(self, dir_name, shortcuts):
        index = 0
        done = False
        new_name = dir_name

        while not done:
            done = True
            for shortcut in shortcuts:
                if shortcut.name() == new_name:
                    index += 1
                    new_name = dir_name + ' ' + str(index)
                    done = False

        return new_name

    def get_category(self, category):
        category_model = None
        cat_models = self._app_store_model.get_categories()
        for cat_model in cat_models:
            if cat_model.name() == category:
                category_model = cat_model.get_applications_set()
                break
        return category_model

    def get_recommended_sites(self):
        return self._sites_provider.get_recommended_sites()

    def set_add_shortcuts_box(self, category, subcategory=''):
        self._add_shortcuts_view.set_add_shortcuts_box(category, subcategory)

    def install_app(self, application_model):
        self._app_store_model.install(application_model)

    def build_shortcut_from_application_model(self, app_model):
        try:
            name = app_model.name()
            key = app_model.id()

            icon = {}
            backup_image = image_util.image_path("endless.png")
            icon['normal'] = app_model.normal_icon() or backup_image
            icon['mouseover'] = app_model.hover_icon() or backup_image
            icon['pressed'] = app_model.down_icon() or backup_image
            shortcut = AppShortcut(key, name, icon)
            return shortcut
        except Exception as e:
            print >> sys.stderr, "error: "+repr(e)
            return None

    def build_shortcut_from_link_model(self, link_model):
        name = self._name_format_util.format(link_model.name())

        key = 'browser'
        icon = {}
        backup_image = self.get_favicon_image_file(link_model._url) or image_util.image_path("endless-browser.png")
        icon['normal'] = link_model.normal_icon() or backup_image
        icon['mouseover'] = link_model.hover_icon() or backup_image
        icon['pressed'] = link_model.down_icon() or backup_image
        parameters = [link_model._url]
        shortcut = AppShortcut(key, name, icon, params=parameters)
        return shortcut

    def _is_image_in_cache(self, filename):
        return os.path.exists(self.IMAGE_CACHE_PATH + filename)

    def get_favicon(self, url):
        if not url.startswith('http'):
            url = 'http://' + url

        filename = 'favicon.' + self._strip_protocol(url) + '.ico'
        filename = filename.replace('/', '_')

        if self._is_image_in_cache(filename):
            return image_util.load_pixbuf(self.IMAGE_CACHE_PATH + filename)
        else:
            try:
                favicon_response = self._url_opener(url+'/favicon.ico')
                
                if self._strip_protocol(favicon_response.geturl()) == self._strip_protocol(url+'/favicon.ico'):
                    fi = open(self.IMAGE_CACHE_PATH + filename, 'wb')
                    fi.write(favicon_response.read())
                    fi.close()

                    try:                    
                        favicon_response.close()
                    except:
                        pass
                    
                    return self._pixbuf_loader(self.IMAGE_CACHE_PATH + filename)
            except:
                print "err"
                return None
        return None

    def get_favicon_image_file(self, url):
        cache_path = os.path.expanduser(self.IMAGE_CACHE_PATH)

        filename = 'favicon.' + self._strip_protocol(url) + '.ico'
        filename = filename.replace('/', '_')
        if not os.path.exists(cache_path+filename):
            if self.get_favicon(url):
                return cache_path+filename
            else:
                return None
        else:
            return cache_path+filename

    def create_link_model(self, url):
        if not url.startswith('http'):
            url = 'http://' + url

        # TODO Why is this even here?  get_favicon should return None if the url is bad
        try:
            connection = self._url_opener(url)
            connection.close()
        except:
            return None

        self.get_favicon(url)
        name = self._strip_protocol(url)
        custom_link_model = LinkModel('', name, url)
        recommended_sites = self.get_recommended_sites()
        link_model = next((model for model in recommended_sites if model == custom_link_model), custom_link_model)
        return link_model

    def _strip_protocol(self, url):
        url = url.replace('http://', '')
        url = url.replace('https://', '')

        return url
