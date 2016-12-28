class NotInitialized(Exception):
    def __init__(self):
        super(NotInitialized, self).__init__(
            "Grammar is not initialized. You should call 'init_grammar'.")
