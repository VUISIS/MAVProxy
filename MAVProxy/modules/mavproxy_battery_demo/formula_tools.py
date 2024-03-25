from typing import Any, Optional

from langchain.chat_models.base import BaseChatModel
from langchain.tools.base import BaseTool
from .prompts import (
    EXPLAIN_QUERY_PROMPT,
    REPAIR_OUTPUT_RETURN,
    OUTPUT_RETURN,
    REPAIR_QUERY_PROMPT,
    FORMULA_CODE_LLM_DESC,
    REPAIR_FORMULA_CODE_LLM_DESC
)
from langchain import LLMChain, PromptTemplate
from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)


class FormulaCodeLLM(BaseTool):
    name = "FormulaCodeLLM"
    description = FORMULA_CODE_LLM_DESC
    llm: BaseChatModel

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> Any:
        explain_template = "{prompt}"
        
        prompt_template = PromptTemplate(
            input_variables=["prompt"],
            template=explain_template,
        )
        
        code_understander_chain = LLMChain(
            llm=self.llm, prompt=prompt_template, output_key="explanation"
        )

        out = code_understander_chain({"prompt":query})

        return_output = OUTPUT_RETURN.format(explanation=out['explanation'])

        return return_output

    async def _arun(
        self,
    ):
        raise NotImplementedError("custom_search does not support async")

class RepairFormulaCodeLLM(BaseTool):
    name = "RepairFormulaCodeLLM"
    description = REPAIR_FORMULA_CODE_LLM_DESC
    llm: BaseChatModel

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None):
        repair_template = "{prompt}"
       
        prompt_template = PromptTemplate(
            input_variables=["prompt"],
            template=repair_template,
        )

        repair_chain = LLMChain(
            llm=self.llm, prompt=prompt_template, output_key="repair"
        )
        
        out = repair_chain({"prompt":query})

        return_output = REPAIR_OUTPUT_RETURN.format(repair=out['repair'])

        return return_output

    async def _arun(
        self,
    ):
        raise NotImplementedError("custom_search does not support async")
