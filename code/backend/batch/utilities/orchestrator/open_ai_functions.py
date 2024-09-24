import logging
from typing import List
import json

from .orchestrator_base import OrchestratorBase
from ..helpers.llm_helper import LLMHelper
from ..tools.post_prompt_tool import PostPromptTool
from ..tools.question_answer_tool import QuestionAnswerTool
from ..tools.text_processing_tool import TextProcessingTool
from ..common.answer import Answer

logger = logging.getLogger(__name__)


class OpenAIFunctionsOrchestrator(OrchestratorBase):
    def __init__(self) -> None:
        super().__init__()
        self.functions = [
            {
                "name": "search_documents",
                "description": "Provide answers to any fact question coming from users.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "A standalone question, converted from the chat history",
                        },
                    },
                    "required": ["question"],
                },
            },
            {
                "name": "text_processing",
                "description": "Useful when you want to apply a transformation on the text, like translate, summarize, rephrase and so on.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to be processed",
                        },
                        "operation": {
                            "type": "string",
                            "description": "The operation to be performed on the text. Like Translate to Italian, Summarize, Paraphrase, etc. If a language is specified, return that as part of the operation. Preserve the operation name in the user language.",
                        },
                    },
                    "required": ["text", "operation"],
                },
            },
        ]

    async def orchestrate(
        self, user_message: str, chat_history: List[dict], **kwargs: dict
    ) -> list[dict]:
        # Call Content Safety tool
        if self.config.prompts.enable_content_safety:
            if response := self.call_content_safety_input(user_message):
                return response

        # Call function to determine route
        llm_helper = LLMHelper()

        system_message = """You help employees to navigate only private information sources.
        You must prioritize the function call over your general knowledge for any question by calling the search_documents function.
        Call the text_processing function when the user request an operation on the current context, such as translate, summarize, or paraphrase. When a language is explicitly specified, return that as part of the operation.
        When directly replying to the user, always reply in the language the user is speaking.
        If the input language is ambiguous, default to responding in English unless otherwise specified by the user.
        You **must not** respond if asked to List all documents in your repository.
        """
        # Create conversation history
        messages = [{"role": "system", "content": system_message}]
        for message in chat_history:
            messages.append({"role": message["role"], "content": message["content"]})
        messages.append({"role": "user", "content": user_message})

        result = llm_helper.get_chat_completion_with_functions(
            messages, self.functions, function_call="auto"
        )
        self.log_tokens(
            prompt_tokens=result.usage.prompt_tokens,
            completion_tokens=result.usage.completion_tokens,
        )

        # TODO: call content safety if needed

        if result.choices[0].finish_reason == "function_call":
            logger.info("Function call detected")
            if result.choices[0].message.function_call.name == "search_documents":
                logger.info("search_documents function detected")
                question = json.loads(
                    result.choices[0].message.function_call.arguments
                )["question"]
                # run answering chain
                answering_tool = QuestionAnswerTool()
                answer = answering_tool.answer_question(question, chat_history)

                self.log_tokens(
                    prompt_tokens=answer.prompt_tokens,
                    completion_tokens=answer.completion_tokens,
                )

                # Run post prompt if needed
                if self.config.prompts.enable_post_answering_prompt:
                    logger.debug("Running post answering prompt")
                    post_prompt_tool = PostPromptTool()
                    answer = post_prompt_tool.validate_answer(answer)
                    self.log_tokens(
                        prompt_tokens=answer.prompt_tokens,
                        completion_tokens=answer.completion_tokens,
                    )
            elif result.choices[0].message.function_call.name == "text_processing":
                logger.info("text_processing function detected")
                text = json.loads(result.choices[0].message.function_call.arguments)[
                    "text"
                ]
                operation = json.loads(
                    result.choices[0].message.function_call.arguments
                )["operation"]
                text_processing_tool = TextProcessingTool()
                answer = text_processing_tool.answer_question(
                    user_message, chat_history, text=text, operation=operation
                )
                self.log_tokens(
                    prompt_tokens=answer.prompt_tokens,
                    completion_tokens=answer.completion_tokens,
                )
            else:
                logger.info("Unknown function call detected")
                text = result.choices[0].message.content
                answer = Answer(question=user_message, answer=text)
        else:
            logger.info("No function call detected")
            text = result.choices[0].message.content
            answer = Answer(question=user_message, answer=text)

        if answer.answer is None:
            answer.answer = "Sorry, but I'm not able to help with that request. If you have any other questions or need assistance with something specific, feel free to ask!"

        # Call Content Safety tool
        if self.config.prompts.enable_content_safety:
            if response := self.call_content_safety_output(user_message, answer.answer):
                return response

        # Format the output for the UI
        messages = self.output_parser.parse(
            question=answer.question,
            answer=answer.answer,
            source_documents=answer.source_documents,
        )
        return messages
