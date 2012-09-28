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
    preferences_provider = DesktopPreferencesDatastore()
    presenter = DesktopPresenter(EndlessDesktopView(preferences_provider), 
                                 EndlessDesktopModel(app_desktop_datastore=DesktopLocaleDatastore(), 
                                                     app_datastore=AppDatastore(), 
                                                     app_launcher=AppLauncher(), 
                                                     feedback_manager=FeedbackManager(), 
                                                     time_provider=TimeProvider(), 
                                                     preferences_provider=preferences_provider))
    presenter._view.main()
        
    
    