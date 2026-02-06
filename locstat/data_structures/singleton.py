import weakref
from typing import Any, Optional

__all__ = ("SingletonMeta",)

class SingletonMeta(type):
    _instance_reference: Optional[weakref.ReferenceType[Any]] = None

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        if not cls._instance_reference:
            _temp_instance: Any = super().__call__(*args, **kwds)
            cls._instance_reference = weakref.ref(_temp_instance,
                                                  lambda _ : setattr(cls, "_instance_reference", None))
        return cls._instance_reference()