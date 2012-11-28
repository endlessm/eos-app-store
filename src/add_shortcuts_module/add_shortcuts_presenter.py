from add_shortcuts_model import AddShortcutsModel
from osapps.app_shortcut import AppShortcut
from osapps.desktop_locale_datastore import DesktopLocaleDatastore
from application_store.application_store_model import ApplicationStoreModel
from shortcut_category import ShortcutCategory
from xdg.DesktopEntry import DesktopEntry
from application_store.recommended_sites_provider import RecommendedSitesProvider
import os
import urllib2
from eos_util import image_util
from desktop_files.link_model import LinkModel

class AddShortcutsPresenter():
    def __init__(self):
        self._model = AddShortcutsModel()
        self._app_desktop_datastore = DesktopLocaleDatastore()
        self._app_store_model = ApplicationStoreModel()
        self._add_shortcuts_view = None #AddShortcutsView()
        self._sites_provider = RecommendedSitesProvider()
        self.IMAGE_CACHE_PATH = '/tmp/'  #maybe /tmp/endless-image-cache/ ?

    def get_category_data(self):
        category_data = self._model.get_category_data()
        app_categories = self._app_store_model.get_categories()
        for category in category_data:
            if category.category == _('APP'):
                for app_category in app_categories:
                    category.subcategories.append(ShortcutCategory(app_category.name()))
                category.subcategories[0].active = True
        return category_data
    
    
    def create_directory(self, dir_name, image_file, presenter):
        shortcuts = presenter._model._app_desktop_datastore.get_all_shortcuts()
        dir_name = self.check_dir_name(dir_name, shortcuts)
        path = self._model.create_directory(dir_name)
        if path:
            shortcut = AppShortcut(key='', name=dir_name, icon={'normal':image_file})
            presenter._model._app_desktop_datastore.add_shortcut(shortcut)
    
    def get_folder_icons(self, path, hint):
        return self._model.get_folder_icons(path, hint)
    
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
    
    def set_add_shortcuts_view(self, view):
        self._add_shortcuts_view = view
        self._add_shortcuts_view.set_presenter(self)
    
    def install_app(self, app):
        self._app_store_model.install(app)
        try:
            de = DesktopEntry()
            de.parse(app._desktop_file_path)
            name = de.getName()
            key = de.getExec()
            icon = {}
            normal = de.get('X-EndlessM-Normal-Icon') or image_util.image_path("endless.png")
            hover = de.get('X-EndlessM-Hover-Icon') or image_util.image_path("endless.png")
            pressed = de.get('X-EndlessM-Down-Icon') or image_util.image_path("endless.png")
            icon['normal'] = normal
            icon['mouseover'] = hover
            icon['pressed'] = pressed
            shortcut = AppShortcut(key, name, icon)
            return shortcut
        except:
            return None


    def install_site(self, site):
        name = self._strip_protocol(site._url)
        
        key = 'browser'
        icon = {}
        normal = self.get_favicon_image_file(site._url) or image_util.image_path("endless-browser.png")
        hover = normal
        pressed = normal
        icon['normal'] = normal
        icon['mouseover'] = hover
        icon['pressed'] = pressed
        parameters = [site._url]
        shortcut = AppShortcut(key, name, icon, params=parameters)
        return shortcut
    
    def get_favicon(self, url):
        cache_path = os.path.expanduser(self.IMAGE_CACHE_PATH)
        if not url.startswith('http'):
            url = 'http://' + url
        
        filename = 'favicon.' + self._strip_protocol(url) + '.ico'
        filename = filename.replace('/', '_')
        
        if os.path.exists(cache_path+filename):
            return image_util.load_pixbuf(cache_path+filename)
        else:
            try:
                favicon_response = urllib2.urlopen(url+'/favicon.ico')
                if self._strip_protocol(favicon_response.geturl()) == self._strip_protocol(url+'/favicon.ico'):
                    fi = open(cache_path+filename, 'wb')
                    fi.write(favicon_response.read())
                    fi.close()
                    return image_util.load_pixbuf(cache_path+filename)
            except:
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
    
    def get_custom_site_shortcut(self, url):
        if not url.startswith('http'):
            url = 'http://' + url
        
        try:
            response = urllib2.urlopen(url)
        except:
            return None
        
        self.get_favicon(url)
        name = self._strip_protocol(url)
        return LinkModel(url, name, url)
    
    def _strip_protocol(self, url):
        if url.startswith('https://'):
            return url[8:]
        elif url.startswith('http://'):
            return url[7:]
        else:
            return url
