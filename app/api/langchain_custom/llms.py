from langchain_openai import ChatOpenAI
from langchain_community.llms.llamafile import Llamafile
from models.model import LLMModel


def is_valid_model_value(model_value):
    return any(model_value == item.value for item in LLMModel)


def load_llm(llm_name: str):
    if llm_name == "Llamafile":
        # llama model server must be running for this
        # https://python.langchain.com/v0.1/docs/use_cases/question_answering/local_retrieval_qa/#llamafile
        # ./TinyLlama-1.1B-Chat-v1.0.Q5_K_M.llamafile --server --nobrowser
        return Llamafile()
    elif is_valid_model_value(llm_name):
        # defaults to openai models
        return ChatOpenAI(temperature=0, model_name=llm_name)
    else:
        raise ValueError(f"Unsupported llm name: {llm_name}")
