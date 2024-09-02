from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field


class SQLResponse(BaseModel):
    """
    Response schema.
    """
    SQLQuery: str = Field(
        ...,
        description="SQL Query to run."
    )


def text_to_sql(
        question: str,
        text2sql_cfg_obj: object,
        llm_config: dict,
        top_k: int = 5,
        verbose: bool = True) -> str:
    """
    Convert plain text to sql using LLM
    Parameters:
        question: str = Plaintext question to convert to sql.
        text2sql_cfg_obj: object = class with prompt template & table info. eg in core/setup.py
        llm_config: dict = dict containing llm params {"model": ..., "temperature": ...}
    """
    assert "model" in llm_config, "Model must be provided (model: ...)"
    assert "temperature" in llm_config, "Temperature must be provided (temperature: ...)"
    text2sql_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", text2sql_cfg_obj.sql_prompt_template),
            ("human", "{input}"),
        ]
    )

    text2sql_model = ChatOpenAI(
        model=llm_config["model"],
        temperature=llm_config["temperature"],
        verbose=verbose,
        ).with_structured_output(SQLResponse)
    text2sql_runnable = text2sql_prompt.partial(
        table_info=text2sql_cfg_obj.table_info, top_k=top_k) | text2sql_model

    # return text2sql_runnable.to_json()['kwargs']['first'].json()
    sql_query = text2sql_runnable \
        .with_config({"run_name": "text2sql_runnable"}) \
        .invoke({"input": question,
                 "table_name": text2sql_cfg_obj.table_name})

    my_sql_query = sql_query.SQLQuery
    my_sql_query.replace("\"", '')
    return my_sql_query
