from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple


IConversation = List[Dict]
IPrompt = str | IConversation


class AbstractModel(ABC):
    @abstractmethod
    def __call__(
        self, prompts: List[IPrompt], max_tokens: Optional[int]
    ) -> Tuple[List[str], Any]:
        """Given batch of prompts, return list of string outputs from a given LLM, and possible meta info about outputs."""
        pass

    @staticmethod
    def to_conversation(prompt: str, system: Optional[str] = None) -> IConversation:
        conversation = [
            {"role": "user", "content": prompt},
        ]
        if system is not None:
            conversation.insert(0, {"role": system, "content": prompt})
        return conversation
