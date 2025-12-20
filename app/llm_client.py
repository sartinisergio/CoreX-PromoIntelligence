"""
llm_client.py
Client per OpenAI API
"""

import os
import json
from typing import Optional
from dataclasses import dataclass

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class LLMResponse:
    content: str
    usage: dict
    success: bool
    error: Optional[str] = None


class OpenAILLMClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.client = None
        
        if HAS_OPENAI and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def _call(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(content="", usage={}, success=False, 
                             error="Client non disponibile")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage={"total_tokens": response.usage.total_tokens},
                success=True
            )
        except Exception as e:
            return LLMResponse(content="", usage={}, success=False, error=str(e))
    
    def label_cluster(self, concept_names: list[str], context: str = "Chimica Organica") -> tuple[str, str]:
        system_prompt = """Sei un esperto di didattica della chimica organica.
Assegna un nome di modulo didattico e una breve descrizione.
Rispondi SOLO in JSON: {"module_name": "...", "description": "..."}"""

        concepts_list = "\n".join(f"- {name}" for name in concept_names[:15])
        user_prompt = f"Concetti:\n{concepts_list}\n\nAssegna nome modulo e descrizione."

        response = self._call(system_prompt, user_prompt)
        
        if not response.success:
            return concept_names[0] if concept_names else "Modulo", ""
        
        try:
            content = response.content.strip()
            if "```" in content:
                content = content.split("```")[1].replace("json", "").strip()
            data = json.loads(content)
            return data.get("module_name", "Modulo"), data.get("description", "")
        except:
            return concept_names[0] if concept_names else "Modulo", ""
    
    def suggest_module_hierarchy(self, module_names: list[str]) -> list[dict]:
        system_prompt = """Ordina i moduli in ordine didattico logico.
Rispondi SOLO in JSON: {"ordered_modules": [{"name": "...", "order": 1, "group": "..."}]}"""

        modules_list = "\n".join(f"- {name}" for name in module_names)
        user_prompt = f"Moduli:\n{modules_list}"

        response = self._call(system_prompt, user_prompt)
        
        if not response.success:
            return [{"name": n, "order": i+1, "group": ""} for i, n in enumerate(module_names)]
        
        try:
            content = response.content.strip()
            if "```" in content:
                content = content.split("```")[1].replace("json", "").strip()
            data = json.loads(content)
            return data.get("ordered_modules", [])
        except:
            return [{"name": n, "order": i+1, "group": ""} for i, n in enumerate(module_names)]


_llm_client: Optional[OpenAILLMClient] = None

def get_llm_client() -> OpenAILLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAILLMClient()
    return _llm_client