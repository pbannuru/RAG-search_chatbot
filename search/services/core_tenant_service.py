from sqlalchemy.orm import Session

from app.dto.tenant import CreateTenantIn
from app.sql_app.dbmodels import core_tenant


class ServiceBase:
    def __init__(self, db: Session):
        self.__db = db

    @property
    def db(self):
        return self.__db


class CoreTenantService(ServiceBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.__model = core_tenant.CoreTenant

    def get_all(self):
        return self.db.query(self.__model).all()

    def get_by_client_id(self, client_id: str):
        return self.db.query(self.__model).filter_by(client_id=client_id).one_or_none()

    def get_one(self, tenant_id: str):
        return self.db.get_one(self.__model, tenant_id)

    def create(self, create_tenant_dto: CreateTenantIn):
        new_tenant = self.__model(**create_tenant_dto.model_dump())
        self.db.add(new_tenant)
        self.db.commit()
        self.db.refresh(new_tenant)

        return create_tenant_dto
