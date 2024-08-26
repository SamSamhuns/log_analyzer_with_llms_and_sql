from langchain_openai import ChatOpenAI
from langchain_community.llms.llamafile import Llamafile
from core.config import LLM_MODEL_NAME


def load_llm(llm_name: str):
    if llm_name == "llamafile":
        # llama model server must be running for this
        # https://python.langchain.com/v0.1/docs/use_cases/question_answering/local_retrieval_qa/#llamafile
        # ./TinyLlama-1.1B-Chat-v1.0.Q5_K_M.llamafile --server --nobrowser
        return Llamafile()
    elif llm_name == "chatopenai":
        return ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-1106")
    else:
        raise ValueError(f"Unsupported llm name: {llm_name}")

# TODO update this file logic to be more robust and more llms
llm = load_llm(LLM_MODEL_NAME)
