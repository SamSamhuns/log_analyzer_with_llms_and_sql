import json
import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

_THINK_BLOCK_RE = re.compile(r"<think>[\s\S]*?(?:</think>|$)", flags=re.IGNORECASE)
_CODE_BLOCK_RE = re.compile(r"```(?:sql)?\s*(.*?)```", flags=re.IGNORECASE | re.DOTALL)
_SQL_START_RE = re.compile(r"\b(SELECT|WITH|SHOW|DESCRIBE|EXPLAIN)\b", flags=re.IGNORECASE)


def _message_to_text(message: Any) -> str:
    """Convert a LangChain message payload into plain text."""
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                text_chunks.append(item)
                continue
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                text_chunks.append(item["text"])
        return "\n".join(text_chunks).strip()
    return str(content)


def _extract_sql_query(raw_output: str) -> str:
    """Extract an executable SQL query from a model response."""
    output = raw_output.strip()
    if not output:
        raise ValueError("LLM returned an empty response while generating SQL.")

    # Some models emit internal reasoning tags in content; strip them.
    output = _THINK_BLOCK_RE.sub("", output).strip()

    if output.startswith("{"):
        try:
            payload = json.loads(output)
            if isinstance(payload, dict) and isinstance(payload.get("SQLQuery"), str):
                output = payload["SQLQuery"].strip()
        except json.JSONDecodeError:
            pass

    code_block_match = _CODE_BLOCK_RE.search(output)
    if code_block_match:
        output = code_block_match.group(1).strip()

    output = output.replace("```sql", "").replace("```", "").strip()
    output = output.strip().strip('"').strip("'").strip()

    sql_start_match = _SQL_START_RE.search(output)
    if sql_start_match:
        output = output[sql_start_match.start() :].strip()

    if ";" in output:
        first_statement, remainder = output.split(";", 1)
        if remainder.strip():
            output = f"{first_statement.strip()};"

    if not output:
        raise ValueError("No SQL query could be extracted from the LLM response.")
    return output


def text_to_sql(
    question: str,
    text2sql_cfg_obj: object,
    llm_config: dict,
    top_k: int = 5,
    verbose: bool = False,
) -> str:
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
            ("system", "Return exactly one SQL query only. Do not include reasoning, markdown, XML tags, or explanations.",),
            ("human", "{input}"),
        ]
    )

    text2sql_model = ChatOpenAI(
        model=llm_config["model"],
        temperature=llm_config["temperature"],
        verbose=verbose,
    )
    text2sql_runnable = text2sql_prompt.partial(table_info=text2sql_cfg_obj.table_info, top_k=top_k) | text2sql_model

    llm_response = text2sql_runnable.with_config({"run_name": "text2sql_runnable"}).invoke(
        {"input": question, "table_name": text2sql_cfg_obj.table_name}
    )
    mysql_query = _extract_sql_query(_message_to_text(llm_response))
    return mysql_query
