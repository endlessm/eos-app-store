class FeedbackPluginPresenter(object):
    def __init__(self, model):
        self._model = model
        #self._view = view
        #self._view.set_presenter(self)

    def submit_feedback(self, message, bug):
        self._model.submit_feedback(message, bug)
