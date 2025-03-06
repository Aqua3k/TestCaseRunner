from dataclasses import dataclass

@dataclass(frozen=True)
class LibraryMetadata:
    LIBRARY_NAME: str = "testcaserunner"
    LIBRARY_VERSION: str = "1.0.0"
