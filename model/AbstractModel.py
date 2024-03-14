from abc import ABC, abstractmethod
from typing import Dict, List, Optional


IConversation = List[Dict]
IPrompt = str | IConversation
IChatOutput = List[str]


class AbstractModel(ABC):
    @abstractmethod
    def __call__(
        self, prompts: List[IPrompt], max_tokens: Optional[int]
    ) -> List[IChatOutput]:
        """Given batch of prompts, return list of string outputs from a given LLM."""
        pass

    @staticmethod
    def to_conversation(prompt: str, system: Optional[str] = None) -> IConversation:
        conversation = [
            {"role": "user", "content": prompt},
        ]
        if system is not None:
            conversation.insert(0, {"role": system, "content": prompt})
        return conversation
