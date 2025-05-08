from fastapi import APIRouter, Depends

from app.dto.feedbacks import (
    CreateFeedbackDto,
    EditFeedbackImpressionDto,
    EditFeedbackTextDto,
)
from app.middlewares.authentication import JWTBearerTenantApiSwaggerAuthenticated
from app.services.isearchui_search_feedback_service import (
    ISearchUISearchFeedbackService,
)
from app.sql_app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/isearchui_search_feedback",
    tags=["isearchui_search_feedback"],
)


@router.get("/")
async def get_feedback(
    db: Session = Depends(get_db),
    dependencies=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
):
    return ISearchUISearchFeedbackService(db).get_feedbacks()


@router.post("/")
async def create_feedback(
    create_feedback_dto: CreateFeedbackDto,
    db: Session = Depends(get_db),
    dependencies=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
):
    return ISearchUISearchFeedbackService(db).create_feedback(create_feedback_dto)


@router.patch("/impression")
async def edit_feedback_impression(
    id: int,
    edit_feedback_dto: EditFeedbackImpressionDto,
    db: Session = Depends(get_db),
    dependencies=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
):
    return ISearchUISearchFeedbackService(db).edit_feedback_impression(
        id, edit_feedback_dto
    )


@router.patch("/feedback_text")
async def edit_feedback_text(
    id: int,
    edit_feedback_dto: EditFeedbackTextDto,
    db: Session = Depends(get_db),
    dependencies=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
):
    return ISearchUISearchFeedbackService(db).edit_feedback_text(id, edit_feedback_dto)
