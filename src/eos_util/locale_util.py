import locale
import os

class LocaleUtil(object):
    '''
    Used for retrieval of currently-set locale
    '''

    DEFAULT_LOCALE = "en_US"

    def get_locale(self):
        lang_code = locale.getdefaultlocale()[0]
        if not lang_code:
            lang_code = self.get_default_locale()

        return lang_code

    def get_default_locale(self):
        return self.DEFAULT_LOCALE

    def append_dir_with_current_locale(self, directory):
        directory_with_locale = os.path.join(directory, self.get_locale())
        if not os.path.isdir(directory_with_locale):
            directory_with_locale = os.path.join(directory, self.get_default_locale())
        return directory_with_locale
    
    def format_date_time(self, timestamp):
        # Note: we keep mixed case month format here
        # The caller is responsible for converting to all caps if desired
        # For now, we assume MMM DD and 12-hour for US, DD MMM and 24-hour elsewhere
        # In the future, we should add support for other countries that use MMM DD,
        # and 12-hour vs. 24-hour should be based on the current system settings
        if 'US' in self.get_locale():
            return timestamp.strftime('%I:%M %p')
        else:
            return timestamp.strftime('%H:%M')
