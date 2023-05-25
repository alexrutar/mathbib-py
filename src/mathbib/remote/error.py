class RemoteError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class RemoteAccessError(RemoteError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RemoteParseError(RemoteError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
