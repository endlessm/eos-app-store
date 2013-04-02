from search_box_constants import SearchBoxConstants

class SearchBoxPresenter(object):
    def __init__(self, view, model):
        view.add_listener(SearchBoxConstants.LAUNCH_BROWSER, lambda: self._launch_browser(view, model))

    def _launch_browser(self, view, model):
        model.search(view.get_search_text())
        view.reset_search()

