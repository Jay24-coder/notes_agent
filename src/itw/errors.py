class ItwError(Exception):
    """Base error with a user-facing message."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
