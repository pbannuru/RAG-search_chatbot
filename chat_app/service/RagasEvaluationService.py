import json
from sqlalchemy.orm import Session
from service.core_tenant_service import ServiceBase
from sql_app.dbmodels.ragas_log import RagasEvaluation
from uuid import UUID

class RagasEvaluationService(ServiceBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.__model = RagasEvaluation

    def get_evaluations(self):
        """Fetch all evaluation records."""
        return self.db.query(self.__model).all()

    async def log_evaluation(
        self,
        session_id: str,
        user_input: str,
        response: str,
        retrieved_contexts: list[str] = None,
        faithfulness_score: float = None,
        context_precision_score: float = None,
        factual_correctness_score: float = None,
    ):
        """Log a new evaluation record."""
        log = self.__model(
            session_id = session_id,
            user_input=user_input,
            response=response,
            retrieved_contexts=json.dumps(retrieved_contexts) if retrieved_contexts else None,
            faithfulness_score=faithfulness_score,
            context_precision_score=context_precision_score,
            factual_correctness_score=factual_correctness_score,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
