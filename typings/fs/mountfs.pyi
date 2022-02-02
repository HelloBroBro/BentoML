import typing
from typing import (
    IO,
    Any,
    BinaryIO,
    Collection,
    Iterator,
    List,
    Optional,
    Text,
    Tuple,
    Union,
)
from .base import FS
from .enums import ResourceType
from .info import Info, RawInfo
from .permissions import Permissions
from .subfs import SubFS

if typing.TYPE_CHECKING:
    M = ...

class MountError(Exception): ...

class MountFS(FS):
    _meta = ...
    def __init__(self, auto_close: bool = ...) -> None: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def mount(self, path: Text, fs: Union[FS, Text]) -> None: ...
    def close(self) -> None: ...
    def desc(self, path: Text) -> Text: ...
    def getinfo(
        self, path: Text, namespaces: Optional[Collection[Text]] = ...
    ) -> Info: ...
    def listdir(self, path: Text) -> List[Text]: ...
    def makedir(
        self, path: Text, permissions: Optional[Permissions] = ..., recreate: bool = ...
    ) -> SubFS[FS]: ...
    def openbin(
        self, path: Text, mode: Text = ..., buffering: int = ..., **kwargs: Any
    ) -> BinaryIO: ...
    def remove(self, path: Text) -> None: ...
    def removedir(self, path: Text) -> None: ...
    def readbytes(self, path: Text) -> bytes: ...
    def download(
        self,
        path: Text,
        file: BinaryIO,
        chunk_size: Optional[int] = ...,
        **options: Any
    ) -> None: ...
    def readtext(
        self,
        path: Text,
        encoding: Optional[Text] = ...,
        errors: Optional[Text] = ...,
        newline: Text = ...,
    ) -> Text: ...
    def getsize(self, path: Text) -> int: ...
    def getsyspath(self, path: Text) -> Text: ...
    def gettype(self, path: Text) -> ResourceType: ...
    def geturl(self, path: Text, purpose: Text = ...) -> Text: ...
    def hasurl(self, path: Text, purpose: Text = ...) -> bool: ...
    def isdir(self, path: Text) -> bool: ...
    def isfile(self, path: Text) -> bool: ...
    def scandir(
        self,
        path: Text,
        namespaces: Optional[Collection[Text]] = ...,
        page: Optional[Tuple[int, int]] = ...,
    ) -> Iterator[Info]: ...
    def setinfo(self, path: Text, info: RawInfo) -> None: ...
    def validatepath(self, path: Text) -> Text: ...
    def open(
        self,
        path: Text,
        mode: Text = ...,
        buffering: int = ...,
        encoding: Optional[Text] = ...,
        errors: Optional[Text] = ...,
        newline: Text = ...,
        **options: Any
    ) -> IO: ...
    def upload(
        self,
        path: Text,
        file: BinaryIO,
        chunk_size: Optional[int] = ...,
        **options: Any
    ) -> None: ...
    def writebytes(self, path: Text, contents: bytes) -> None: ...
    def writetext(
        self,
        path: Text,
        contents: Text,
        encoding: Text = ...,
        errors: Optional[Text] = ...,
        newline: Text = ...,
    ) -> None: ...