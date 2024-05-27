import os
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from .AbstractModel import AbstractModel, IPrompt
from typing import List, Tuple, Optional, Callable, Any, cast
import config

logger = config.get_logger(__name__)

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
    # https://platform.openai.com/docs/models/gpt-4-turbo-and-gpt-4
    "gpt-4-turbo-2024-04-09": [10.0, 30.0],
    "gpt-4-0125-preview": [10.0, 30.0],  # also turbo despite name
}

# convert to price / token
PRICES = {k: [p / 1_000_000 for p in v] for k, v in PRICES.items()}


class GPTModel(AbstractModel):
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo-0125"):
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key)
        if model_name not in PRICES.keys():
            logger.warning(f"price entry unknown for model '{model_name}'")

    def __call__(
        self,
        prompts: List[IPrompt],
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        temperature: Optional[float] = 1,
        top_p: Optional[float] = None,
    ) -> Tuple[List[str], List[ChatCompletion]]:
        """
        https://platform.openai.com/docs/api-reference/chat/create#chat-create-temperature
        https://community.openai.com/t/cheat-sheet-mastering-temperature-and-top-p-in-chatgpt-api/172683
        """
        assert isinstance(prompts, list)
        extra_args: dict[str, Any] = dict()
        if json_mode:
            # https://platform.openai.com/docs/guides/text-generation/json-mode
            extra_args["response_format"] = {"type": "json_object"}
        if max_tokens is not None:
            extra_args["max_tokens"] = max_tokens
        if temperature is not None:
            extra_args["temperature"] = temperature
        if top_p is not None:
            extra_args["top_p"] = top_p

        logger.debug(f"prompting {self.model_name} with {len(prompts)} prompts")
        completions = []
        raw_outputs = []
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
            raw_outputs.append(completion.choices[0].message.content)
            completions.append(completion)
        return raw_outputs, completions

    @staticmethod
    def compute_price(completions: ChatCompletion | List[ChatCompletion]) -> float:
        """Compute USD price of give API request(s)."""
        if not isinstance(completions, list):
            completions = [completions]

        total_price = 0.0
        for c in completions:
            prompt_price, completion_price = PRICES[c.model]
            if c.model not in PRICES:
                logger.warning(f"price entry unknown for model '{c.model}'")
                continue
            total_price += (
                prompt_price * c.usage.prompt_tokens
                + completion_price * c.usage.completion_tokens
            )
        return total_price


def auto_reprompt(
    validator: Callable,
    max_retries: int,
    model: GPTModel,
    prompts: List[IPrompt],
    **kwargs,
) -> Tuple[List[Optional[str]], float, int]:
    """
    Keep prompting model until validator function is happy or a depth of max_retries iterations are reached.
    max_retries is the max number of retry iterations e.g. one retry would be: 3 failures in first batch -> second batch of length 3 which all validate
    So in the worst case, one "retry" could mean the model is prompted twice with batch size len(prompts).
    """
    assert isinstance(max_retries, int)
    assert isinstance(prompts, list)

    outputs, meta = model(prompts, **kwargs)
    total_price = model.compute_price(meta)
    total_calls = len(outputs)
    # orig_outputs = outputs.copy()

    new_outputs = cast(list[Optional[str]], outputs)

    # map indices to {new_prompt}
    bad = {}
    for i, response in enumerate(new_outputs):
        if not validator(response):
            bad[i] = {"new_prompt": prompts[i]}
            new_outputs[i] = None

    max_retries -= 1
    if len(bad) == 0 or max_retries < 0:
        return new_outputs, total_price, total_calls

    new_prompts = [v["new_prompt"] for v in bad.values()]
    logger.debug(f"reprompting {len(new_prompts)} prompts ({max_retries=})")
    new_outputs, new_price, new_calls = auto_reprompt(
        validator, max_retries, model, new_prompts, **kwargs
    )
    total_calls += new_calls

    cur = 0
    for i in range(len(new_outputs)):
        if i in bad:
            new_outputs[i] = new_outputs[cur]
            cur += 1

    total_price += new_price
    return new_outputs, total_price, total_calls
