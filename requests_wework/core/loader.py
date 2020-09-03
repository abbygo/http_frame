import types
from typing import Text, Dict, Callable

from requests_wework import builtin


def load_module_functions(module) -> Dict[Text, Callable]:
    """ load python module functions.

    Args:
        module: python module

    Returns:
        dict: functions mapping for specified python module

            {
                "func1_name": func1,
                "func2_name": func2
            }

    """
    module_functions = {}

    for name, item in vars(module).items():
        if isinstance(item, types.FunctionType):
            module_functions[name] = item

    return module_functions


def load_builtin_functions() -> Dict[Text, Callable]:
    """ load builtin module functions
    """
    return load_module_functions(builtin)