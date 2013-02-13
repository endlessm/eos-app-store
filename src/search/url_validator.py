import re

class UrlValidator():
    def validate(self, url):
        return self._has_no_whitespace(url) and self._has_a_dot(url)

    def _has_no_whitespace(self, url):
        return not re.match(r"^\S*\s+\S*$", url)

    def _has_a_dot(self, url):
        return re.match(r"^.*\..*$", url)
