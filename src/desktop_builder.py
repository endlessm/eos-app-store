import sys

from desktop.endless_desktop_presenter import DesktopPresenter
from desktop.endless_desktop_view import EndlessDesktopView
from desktop.endless_desktop_service import EndlessDesktopService

from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore
from desktop.endless_desktop_model import EndlessDesktopModel
from osapps.app_launcher import AppLauncher
from osapps.app_datastore import AppDatastore
from osapps.desktop_locale_datastore import DesktopLocaleDatastore

def build_desktop():
    preferences_provider = DesktopPreferencesDatastore.get_instance()
    view = EndlessDesktopView()
    model = EndlessDesktopModel(DesktopLocaleDatastore(),
                              preferences_provider,
                              AppDatastore(),
                              AppLauncher())
    presenter = DesktopPresenter(view, model)
    EndlessDesktopService(presenter).start_service()

    if len(sys.argv) > 1 and sys.argv[1] == 'uat':
        from uat.uat_helper import UatHelper
        UatHelper().setup(view)

