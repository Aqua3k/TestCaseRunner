import pandas as pd

class RunnerLog:
    def __init__(self, contents: dict, metadata: dict) -> None:
        self._df = pd.DataFrame(contents)
        self._metadata = metadata
    
    def get_dataframe(self) -> pd.DataFrame:
        return self._df
    
    def get_metadata(self) -> dict:
        return self._metadata
