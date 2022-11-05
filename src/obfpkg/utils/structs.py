import os
from pathlib import Path
from typing import Optional, Union, Tuple, List, Callable
from dataclasses import dataclass
from argparse import ArgumentTypeError
from enum import Enum


@dataclass
class Exist:
    # Existance Options
    check: Optional[bool] = None  # File/folder must exist. None for reguardless
    empty_or_not_exist: bool = False  # Must *not* exist or empty directory


@dataclass
class PathDetail:
    name: str
    validator: Callable[[str], bool]


class PathType(Enum):
    # Types allowed for files.
    FILE = PathDetail("file", os.path.isfile)
    DIR = PathDetail("directory", os.path.isdir)
    SYM = PathDetail("symlink", os.path.islink)
    ALL = PathDetail("any", lambda x: True)  # Any thing is fine (don't check)


class PathCheck:
    def __init__(
        self,
        exists: Exist,
        ptype: Union[
            PathType, List[PathType], Tuple[PathType, ...], Callable[..., bool]
        ],
        dash_ok: bool = True,
    ):
        """
        exists:
             Exist(True): a path that does exist
             Exist(False): a path that does not exist, in a valid parent directory
             Exist(None): don't care; reguardless
        type: Type.FILE, Type.DIR, Type.SYM, Type.ALL, a list of these,
              or a function returning True for valid paths
              If None, the type of file/directory/symlink is not checked.
        dash_ok: whether to allow "-" as stdin/stdout
        """
        assert isinstance(exists, Exist)

        # Make sure type is file, dir, sym, None, list, or callable.
        if isinstance(ptype, (list, tuple)):
            # Type is a list, make sure that it includes only "file", "dir"
            # or "sym"
            for t in ptype:
                assert isinstance(t, PathType)

            # Type is the contains check for this lists.
            ptype = ptype.__contains__

        elif not callable(ptype):
            # Otherwise, make sure this is valid.
            assert isinstance(ptype, PathType)

        # else; type is a callable object, and this is ok.

        self._exists = exists
        self._type = ptype
        self._dash_ok = dash_ok

    def __call__(self, string: str):
        if string == "-":
            # the special argument "-" means sys.std[in/out]
            if self._type == PathType.DIR:
                raise ArgumentTypeError(
                    "standard input/output (-) not allowed as directory path"
                )
            elif self._type == PathType.SYM:
                raise ArgumentTypeError(
                    "standard input/output (-) not allowed as symlink path"
                )
            elif not self._dash_ok:
                raise ArgumentTypeError("standard input/output (-) not allowed")
            return string  # No reason to check anything else if this works.

        # If the path must exist.
        if self._exists.check:
            if not os.path.exists(string):
                raise ArgumentTypeError(f"path does not exist: {string}")

            # check PathTypes
            for label, detail in PathType.__members__.items():
                if self._type == getattr(PathType, label):
                    if not detail.value.validator(string):
                        raise ArgumentTypeError(f"path is not a {detail.value.name}: {string}")
                    break
            else:
                # Otherwise, call type.
                if callable(self._type):
                    if not self._type(string):
                        raise ArgumentTypeError(f"path not valid: {string}")
                else:
                    raise ArgumentTypeError(f"path not valid: {string}")

        else:
            if os.path.exists(string):
                if self._exists.empty_or_not_exist:
                    if os.listdir(string):
                        raise ArgumentTypeError(f"path not empty: {string}")

            p = os.path.dirname(string) or os.path.curdir
            if not os.path.exists(p):
                raise ArgumentTypeError("parent directory does not exist: %r" % p)
            elif not os.path.isdir(p):
                raise ArgumentTypeError("parent path is not a directory: %r" % p)

        return Path(string)
