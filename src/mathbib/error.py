class RemoteAccessError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RemoteParseError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
