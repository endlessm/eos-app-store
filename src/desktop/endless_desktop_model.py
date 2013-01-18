from eos_util import image_util
from eos_log import log
from application_store.installed_applications_model import InstalledApplicationsModel
from desktop.list_paginator import ListPaginator

class EndlessDesktopModel(object):
    def __init__(self, app_desktop_datastore, preferences_provider, app_datastore, app_launcher, installed_app_model=InstalledApplicationsModel(), paginator=ListPaginator(page_size=27)):
        self._app_launcher = app_launcher
        self._app_desktop_datastore = app_desktop_datastore
        self._app_datastore = app_datastore
        self._preferences_provider = preferences_provider
        self._installed_applications_model = installed_app_model
        self._paginator = paginator

    def get_shortcuts(self, force=False):
        all_shortcuts = self._app_desktop_datastore.get_all_shortcuts(force=force)
        self._paginator.adjust_list_of_items(all_shortcuts)
        return self._paginator.current_page()

    def set_shortcuts_by_name(self, shortcuts_names):
        self._app_desktop_datastore.set_all_shortcuts_by_name(shortcuts_names)

    def set_shortcuts(self, shortcuts):
        self._app_desktop_datastore.set_all_shortcuts(shortcuts)

    def _relocate_shortcut_to_root(self, source_shortcut):
        source_parent = source_shortcut.parent()
        source_parent.remove_child(source_shortcut)

        all_shortcuts = self._app_desktop_datastore.get_all_shortcuts()
        all_shortcuts.append(source_shortcut)
        self._app_desktop_datastore.set_all_shortcuts(all_shortcuts)
        return True

    def _relocate_shortcut_to_folder(self, source_shortcut, folder_shortcut):
        source_parent = source_shortcut.parent()
        all_shortcuts = self._app_desktop_datastore.get_all_shortcuts()

        if (source_parent is None) and (source_shortcut in all_shortcuts):
            all_shortcuts.remove(source_shortcut)
            folder_shortcut.add_child(source_shortcut)
            self._app_desktop_datastore.set_all_shortcuts(all_shortcuts)
            return True
        elif source_parent is not None:
            source_parent.remove_child(source_shortcut)
            folder_shortcut.add_child(source_shortcut)
            self._app_desktop_datastore.set_all_shortcuts(all_shortcuts)
            return True
        else:
            log.error("unknown shortcut location")
        return False

    def relocate_shortcut(self, source_shortcut, folder_shortcut):
        if source_shortcut is not None:
            source_parent = source_shortcut.parent()

            if folder_shortcut is None:
                if source_parent is not None:
                    return self._relocate_shortcut_to_root(source_shortcut)
            else:
                return self._relocate_shortcut_to_folder(
                    source_shortcut,
                    folder_shortcut
                    )
        return False

    def execute_app(self, app_key, params):
        self._app_launcher.launch_desktop(app_key, params)

    def set_background(self, filename):
        new_image_path = image_util.image_path(filename)
        self._preferences_provider.set_background(new_image_path)

    def get_background_image(self):
        return self._preferences_provider.get_background_image()

    def get_default_background(self):
        return self._preferences_provider.get_default_background()

    def delete_shortcut(self, shortcut):
        all_shortcuts = self._app_desktop_datastore.get_all_shortcuts()
        parent = shortcut.parent()

        success = False
        if parent is not None:
            success = self.delete_from_folder(shortcut, parent)
        else:
            if shortcut in all_shortcuts:
                success = self.delete_from_desktop(shortcut, all_shortcuts)
            else:
                log.error("delete shortcut failed!")

        if success:
            try:
                log.info("successfully removed shortcut from desktop, now removing from json...")
                self._app_desktop_datastore.set_all_shortcuts(all_shortcuts)
                # TODO This could probably be handled better so that we don't
                # try to uninstall a shortcut for a website or folder
                # For now, let's simply catch and discard the exception
                # that results from trying to uninstall a shortcut that
                # is for something other than an application
                try:
                    self._installed_applications_model.uninstall(shortcut.key())
                except:
                    pass
                return True
            except:
                log.error("delete shortcut failed!")
        return False

    def delete_from_folder(self, shortcut, parent):
        try:
            parent.remove_child(shortcut)
            return True
        except:
            log.error("removing child from folder failed!")
        return False

    def delete_from_desktop(self, shortcut, all_shortcuts):
        try:
            log.info("delete shortcut: "+repr(shortcut.key()))
            if shortcut in all_shortcuts:
                all_shortcuts.remove(shortcut)
            else:
                log.info("didn't find shortcut in list: " + repr(shortcut))
            return True
        except Exception as e:
            log.error("no shortcut on desktop!", e)
        return False
    
    def get_page_number(self):
        return self._paginator.current_page_number()
    
    def next_page(self):
        self._paginator.next()

    def previous_page(self):
        self._paginator.prev()
        
    def go_to_page(self, page_index):
        self._paginator.go_to_page(page_index)
        
    def get_total_pages(self):
        return self._paginator.number_of_pages()
