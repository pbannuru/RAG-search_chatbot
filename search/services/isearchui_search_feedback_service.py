from datetime import datetime
from sqlalchemy.orm import Session

from app.dto.feedbacks import (
    CreateFeedbackDto,
    EditFeedbackImpressionDto,
    EditFeedbackTextDto,
)
from app.sql_app.dbmodels import isearchui_search_feedback


class ISearchUISearchFeedbackService:
    def __init__(self, db: Session):
        self.db = db

    def get_feedbacks(self):
        return self.db.query(isearchui_search_feedback.ISearchUISearchFeedback).all()

    def create_feedback(self, create_deedback_dto: CreateFeedbackDto):
        obj = isearchui_search_feedback.ISearchUISearchFeedback(
            **create_deedback_dto.model_dump()
        )
        obj.feedback_timestamp = datetime.now()
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def edit_feedback_impression(
        self, id: int, edit_feedback_dto: EditFeedbackImpressionDto
    ):

        # obj.impression = edit_feedback_dto.impression
        self.db.query(isearchui_search_feedback.ISearchUISearchFeedback).filter(
            isearchui_search_feedback.ISearchUISearchFeedback.id == id
        ).update({"impression": edit_feedback_dto.impression})

        self.db.commit()
        return {"update": "success"}

    def edit_feedback_text(self, id: int, edit_feedback_dto: EditFeedbackTextDto):

        # obj.impression = edit_feedback_dto.impression
        self.db.query(isearchui_search_feedback.ISearchUISearchFeedback).filter(
            isearchui_search_feedback.ISearchUISearchFeedback.id == id
        ).update({"feedback_text": edit_feedback_dto.feedback_text})

        self.db.commit()
        return {"update": "success"}
