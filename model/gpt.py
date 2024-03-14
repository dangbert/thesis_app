import os
from openai import OpenAI
from AbstractModel import AbstractModel, IPrompt, IChatOutput
from typing import List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(SCRIPT_DIR, ".env")

# prices per 1M tokens:
#   https://openai.com/pricing#language-models
#   https://platform.openai.com/docs/models/overview
PRICES = {
    # instruct is less chatty and more concise
    #  https://community.openai.com/t/instructgpt-vs-gpt-3-5-turbo/434241/2
    # [input,output] prices
    "gpt-3.5-turbo-0125": [0.5, 1.5],
    "gpt-3.5-turbo-instruct": [1.5, 2.0],
    "gpt-4-0125-preview": [10.0, 30.0],
}

# convert to price / token
PRICES = {k: [p / 1_000_000 for p in v] for k, v in PRICES.items()}


class GPTModel(AbstractModel):
    def __init__(self, model_name: str = "gpt-3.5-turbo-0125"):
        self.model_name = model_name
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # assert model_name in PRICES.keys()

    # TODO: change output type hint
    def __call__(
        self,
        prompts: List[IPrompt],
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> List[IChatOutput]:
        assert isinstance(prompts, list)
        extra_args = dict()
        if json_mode:
            # https://platform.openai.com/docs/guides/text-generation/json-mode
            extra_args["response_format"] = {"type": "json_object"}
        if max_tokens is not None:
            extra_args["max_tokens"] = max_tokens

        completions = []
        for prompt in prompts:
            if isinstance(prompt, str):
                prompt = self.to_conversation(prompt)

            # TODO more efficient batch requests?
            # https://platform.openai.com/docs/guides/rate-limits/error-mitigation?context=tier-free
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=prompt,
                **extra_args,
            )
            completions.append(completion)
        return completions
