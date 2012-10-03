#!/usr/bin/env python
from desktop.endless_desktop_presenter import DesktopPresenter
from desktop.endless_desktop_view import EndlessDesktopView

from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore
from desktop.endless_desktop_model import EndlessDesktopModel
from metrics.time_provider import TimeProvider
from util.feedback_manager import FeedbackManager
from osapps.app_launcher import AppLauncher
from osapps.app_datastore import AppDatastore
from osapps.desktop_locale_datastore import DesktopLocaleDatastore

if __name__ == "__main__":
    preferences_provider = DesktopPreferencesDatastore.get_instance()
    
    presenter = DesktopPresenter(EndlessDesktopView(), 
                                 EndlessDesktopModel(DesktopLocaleDatastore(),
                                                     preferences_provider, 
                                                     AppDatastore(), 
                                                     AppLauncher(), 
                                                     FeedbackManager(), 
                                                     TimeProvider())
                                                     )
    presenter._view.main()
        
    
    