from datetime import datetime
from sqlalchemy.orm import Session

from app.dto.feedbacks import (
    CreateFeedbackDto,
    EditFeedbackImpressionDto,
    EditFeedbackTextDto,
)
from app.dto.isearchui_users import CreateUserDto
from app.sql_app.dbmodels import isearchui_search_feedback, isearchui_user


class ISearchUIUsersService:
    __model = isearchui_user.ISearchUIUser

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, email: str):

        user = self.db.query(self.__model).filter_by(email=email).one_or_none()

        # if user == None: # TODO: Uncomment this to enable access to all users
        #     user = self.create_user(CreateUserDto(email=email))
        return user

    def create_user(self, user: CreateUserDto):
        user = self.__model(**user.model_dump())
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_users(self):
        return self.db.query(self.__model).all()

    def get_user(self, email: str):
        return self.db.get_one(self.__model, email)

    def get_user_for_ui(self, email: str):
        access_internal = False
        try:
            user = self.db.get_one(self.__model, email)
            print(user.role)
            if user.role == isearchui_user.RoleEnum.Admin:
                access_internal = True
            else:
                access_internal = False

            return {"user": user, "access_internal": access_internal}

        except Exception as e:
            print(e)
            return {"access_internal": access_internal}
