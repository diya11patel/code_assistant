
from pydantic import BaseModel, Field
from dto.value_objects import UserQueryAnalysisType


class QueryAnalysis(BaseModel):
    """
    A single class to represent the outcome of a user query analysis.
    It specifies the type of outcome and the corresponding content.
    """
    type: UserQueryAnalysisType = Field(..., description=f"The type of analysis result is strictly one of the values: {[analysis.value for analysis in UserQueryAnalysisType]}")
    response: str = Field(..., description="The actual content: a direct answer if question is not related to codebase, the corrected and rephrased codebase question if query is code base related or an error message.")
