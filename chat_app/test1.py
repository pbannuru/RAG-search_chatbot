
import ast
import json
import re
import uuid
import asyncio
import pytest
import pytest_asyncio
from service.chatapi_service import fetch_result
from langchain_openai import AzureChatOpenAI
from ragas import SingleTurnSample
from ragas.metrics import Faithfulness
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import LLMContextPrecisionWithoutReference
from ragas.metrics import ResponseRelevancy, FactualCorrectness, LLMContextRecall
from utils.opensearch_utils import OpenSearchUtils
import csv
from service.RagasEvaluationService import RagasEvaluationService
from sql_app.database import DbDepends

# Initialize OpenSearch
OpenSearchUtils.init()

AZURE_OPENAI_ENDPOINT = "https://oai-ceast-hally-sandbox.openai.azure.com/"
AZURE_OPENAI_API_KEY = "e52a924ffe3541189d3d46a24f0afb64"
AZURE_OPENAI_API_VERSION = "2024-06-01"
AZURE_OPENAI_DEPLOYMENT_ID = "gpt-4o"
# Initialize the LLM

llm = AzureChatOpenAI(
    openai_api_version=AZURE_OPENAI_API_VERSION,
    openai_api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    deployment_name=AZURE_OPENAI_DEPLOYMENT_ID,
)

@pytest.fixture(scope="session")
def session_id():
    return str(uuid.uuid4())

# Load user inputs and ground truth from JSON file
with open("test_data.json", "r", encoding="utf-8") as f:
    user_data = json.load(f)

@pytest.mark.asyncio
@pytest.mark.parametrize("data", user_data)
async def test_faithfulness(data,session_id):
    """Fetches results for each query and evaluates faithfulness, storing results in the database."""

    user_input = data["question"]
    ground_truth = data["reference"]

    # Fetch result from search function
    result = await fetch_result(
        search_query=user_input,
        domain="Indigo",
        device="",
        persona="Engineer",
        size=20,
        source=["alias-kaas-phase2", "alias-docebo-phase2", "alias-knowledge-phase2"],
        language="en",
    )

    response = result["content"]
    retrieved_contexts = re.findall(r"page_content='(.*?)'(?:,|\))", result["citations"], re.DOTALL)
    retrieved_contexts_str = json.dumps(retrieved_contexts, ensure_ascii=False)

    # Initialize Langchain wrapper and Ragas metrics
    langchain_llm = LangchainLLMWrapper(llm)
    context_precision = LLMContextPrecisionWithoutReference(llm=langchain_llm)
    faithful = Faithfulness(llm=langchain_llm)
    factual_correctness = FactualCorrectness(llm=langchain_llm)

    sample = SingleTurnSample(
        user_input=user_input,
        response=response,
        retrieved_contexts=retrieved_contexts,
        reference=ground_truth,
    )

    # Compute evaluation scores
    context_precision_score = await context_precision.single_turn_ascore(sample)
    faithfulness_score = await faithful.single_turn_ascore(sample)
    factual_correctness_score = await factual_correctness.single_turn_ascore(sample)
    print(context_precision_score,faithfulness_score,factual_correctness_score)
    # Store results in the database using DbDepends
    with DbDepends() as db:
        ragas_service = RagasEvaluationService(db)
        await ragas_service.log_evaluation(
            session_id =session_id,
            user_input=user_input,
            response=response,
            retrieved_contexts=retrieved_contexts_str,
            faithfulness_score=faithfulness_score,
            context_precision_score=context_precision_score,
            factual_correctness_score=factual_correctness_score,
        )

    # Assertions to ensure evaluation scores are above a threshold
    assert faithfulness_score > 0.7, f"Faithfulness score too low for input: {user_input}"
    assert context_precision_score > 0.7, f"Context precision score too low {context_precision_score} for input: {user_input}"
    assert factual_correctness_score > 0.7, f"Factual correctness score too low {factual_correctness_score} for input: {user_input}"




# # # # Run the test manually
# # import asyncio
# # asyncio.run(test_faithfulness(user_data))


# import ast
# import json
# import re
# import asyncio
# import pytest
# import pytest_asyncio
# from service.chatapi_service import fetch_result
# from langchain_openai import AzureChatOpenAI
# from ragas import SingleTurnSample
# from ragas.metrics import Faithfulness
# from ragas.llms import LangchainLLMWrapper
# from ragas.metrics import LLMContextPrecisionWithoutReference
# from ragas.metrics import ResponseRelevancy, FactualCorrectness, LLMContextRecall
# from utils.opensearch_utils import OpenSearchUtils
# import csv
# # Initialize OpenSearch
# OpenSearchUtils.init()
# AZURE_OPENAI_ENDPOINT = "https://oai-ceast-hally-sandbox.openai.azure.com/"
# AZURE_OPENAI_API_KEY = "e52a924ffe3541189d3d46a24f0afb64"
# AZURE_OPENAI_API_VERSION = "2024-06-01"
# AZURE_OPENAI_DEPLOYMENT_ID = "gpt-4o"
# # Initialize the LLM

# llm = AzureChatOpenAI(
#     openai_api_version=AZURE_OPENAI_API_VERSION,
#     openai_api_key=AZURE_OPENAI_API_KEY,
#     azure_endpoint=AZURE_OPENAI_ENDPOINT,
#     deployment_name=AZURE_OPENAI_DEPLOYMENT_ID,
# )



# # CSV_FILE = "faithfulness_scores1.csv"
# # TEXT_FILE = "citations_with_user_input1.txt"

# # # Write header to CSV file if it doesn't exist
# # with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
# #     writer = csv.writer(file)
# #     writer.writerow(["User Input", "Response", "Retrieved Contexts", "Faithfulness Score", "Context Precision Score","factual_correctness_score"])

# # Load user inputs and ground truth from JSON file
# with open('test_data1.json', 'r', encoding='utf-8') as f:
#     user_data = json.load(f)

# @pytest.mark.asyncio
# @pytest.mark.parametrize("data", user_data)
# async def test_faithfulness(data):
#     """Fetches results for each query and evaluates faithfulness"""

#     user_input = data['question']
#     ground_truth = data['reference']

#     result = await fetch_result(
#         search_query=user_input,
#         domain='Indigo',
#         device='',
#         persona='Engineer',
#         size=5,
#         source=["alias-kaas-phase2", "alias-docebo-phase2", "alias-knowledge-phase2"], 
#         language='en'
#     )

#     response = result['content']
#     retrieved_contexts = re.findall(r"page_content='(.*?)'(?:,|\))", result["citations"], re.DOTALL)

#     langchain_llm = LangchainLLMWrapper(llm)
#     context_precision = LLMContextPrecisionWithoutReference(llm=langchain_llm)
#     faithful = Faithfulness(llm=langchain_llm)
#     # relevance = ResponseRelevancy(llm=langchain_llm)
#     factual_correctness=FactualCorrectness(llm=langchain_llm)

#     sample = SingleTurnSample(
#         user_input=user_input,
#         response=response,
#         retrieved_contexts=retrieved_contexts,
#         reference=ground_truth
#     )
    
#     context_precision_score = await context_precision.single_turn_ascore(sample)
#     faithfulness_score = await faithful.single_turn_ascore(sample)
#     factual_correctness_score = await factual_correctness.single_turn_ascore(sample)
#     # Write results to CSV file
#     retrieved_contexts_str = json.dumps(retrieved_contexts, ensure_ascii=False)
#     # with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
#     #     writer = csv.writer(file)
#     #     writer.writerow([user_input, response, retrieved_contexts_str, faithfulness_score, context_precision_score,factual_correctness_score])

#     # Write to text file
#     # with open(TEXT_FILE, "a", encoding="utf-8") as file:
#     #     file.write(f"User Input: {user_input}\n")
#     #     file.write(f"Ground Truth: {ground_truth}\n")
#     #     file.write(f"Retrieved Contexts: {result['citations']}\n\n")

#     # Assert that faithfulness and context precision scores are above 0.7
#     assert faithfulness_score > 0.7, f"Faithfulness score too low for input: {user_input}"
#     assert context_precision_score > 0.7, f"Context precision score too low {context_precision_score} for input: {user_input}"
#     assert factual_correctness_score>0.7, f"response_relevance_score too low {factual_correctness_score} for input: {user_input}"

