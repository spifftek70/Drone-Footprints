class Color(object):
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    DARKMAGENTA = "\033[0,35m",
    DARKGREEN = "\033[0,32m",

    def __init__(self):
        self.color = self.PURPLE
        self.color = self.BLUE
        self.color = self.GREEN
        self.color = self.YELLOW
        self.color = self.RED
        self.color = self.BOLD
        self.color = self.UNDERLINE
        self.color = self.END
        self.color = self.DARKMAGENTA