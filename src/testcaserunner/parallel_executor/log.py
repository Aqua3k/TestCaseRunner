import pandas as pd
from dataclasses import dataclass

@dataclass
class Metadata:
    library_name: str
    library_version: str
    created_date: str
    attributes: list[str]

    @staticmethod
    def load(metadata: dict) -> 'Metadata':
        # NOTE: 今は大丈夫だが、ライブラリのバージョンを見てロードするデータを変える必要が出るかも
        return Metadata(
            library_name=metadata["library_name"],
            library_version=metadata["library_version"],
            created_date=metadata["created_date"],
            attributes=metadata["attributes"]
        )

class RunnerLog:
    def __init__(self, contents: dict, metadata: dict) -> None:
        self._df = pd.DataFrame(contents)
        self._metadata = metadata
    
    def get_dataframe(self) -> pd.DataFrame:
        return self._df
    
    def get_metadata(self) -> Metadata:
        return Metadata.load(self._metadata)
