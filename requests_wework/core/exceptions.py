
class MyBaseFailure(Exception):
    pass


class ParseTestsFailure(MyBaseFailure):
    pass


class ValidationFailure(MyBaseFailure):
    pass

class FileNotFound(FileNotFoundError, Exception):
    pass

""" error type exceptions
    these exceptions will mark test as error
"""


class MyBaseError(Exception):
    pass




class ParamsError(MyBaseError):
    pass
class NotFoundError(MyBaseError):
    pass





class FunctionNotFound(NotFoundError):
    pass




class VariableNotFound(NotFoundError):
    pass


class EnvNotFound(NotFoundError):
    pass
