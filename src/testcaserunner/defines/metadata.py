from dataclasses import dataclass, field

@dataclass(frozen=True)
class RunnerMetadata:
    LIB_NAME: str = "testcaserunner"
    LIB_VERSION: str = "1.0.0"