from app.llm.llm_config import LLMClient, LLMSolverState
from app.llm.llm_test_solver import LLMTestSolverAgent
from app.schemas.llm import LLMQuestionsListIn, LLMQuestionIn

llm_client = LLMClient()                        # создаём экземпляр
solver_agent = LLMTestSolverAgent(llm_client)
question = LLMQuestionIn(
    **{"id": 1187272786, "type": {"type_id": 2, "description": "Multiple choice (select one option)"},
     "options": ["prog", "creep", "looser", "clown"], "question": "Who are you"})
# передаём объект, а не класс
state = LLMSolverState(
    questions=LLMQuestionsListIn(
        questions=[question]
    ),
    attempts=0,
    raw_answers=None,
    validated_answers=None,
    errors=None
)

# 4. Запускаем решение
result = solver_agent.solve(state)
print(result)