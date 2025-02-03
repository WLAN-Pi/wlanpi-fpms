class Alert():
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def display_popup_alert(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class SimpleTable():
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def display_simple_table(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
