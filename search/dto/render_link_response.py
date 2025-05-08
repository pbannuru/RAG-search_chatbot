from pydantic import BaseModel
 
 
class RenderLinkResponse(BaseModel):
    documentID: str
    render_link: str