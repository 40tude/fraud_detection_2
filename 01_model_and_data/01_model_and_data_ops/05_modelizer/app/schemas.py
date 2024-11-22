from pydantic import BaseModel
from typing import List, Union

class InputData(BaseModel):
    columns: List[str]
    index: List[int]
    data: List[List[Union[str, int, float]]]
