"""
CoreX - LLM Provider v1.0
Supporto multi-provider per estrazione concetti
"""

import json
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class LLMProvider(ABC):
    """Classe base astratta per tutti i provider LLM"""
    
    def __init__(self, api_key: str, model: str, temperature: float = 0.3, max_tokens: int = 2000):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = None
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self):
        pass
    
    @abstractmethod
    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        pass
    
    def extract_concepts(self, text: str, materia: str) -> List[str]:
        system_prompt = """Sei un esperto accademico. Estrai concetti chiave da programmi universitari. 
Rispondi SOLO con JSON valido, un array di stringhe."""
        
        user_prompt = f"""Analizza questo programma universitario di {materia} ed estrai TUTTI i concetti chiave.

TESTO DEL PROGRAMMA:
{text}

ISTRUZIONI:
1. Estrai ogni concetto, argomento o tema specifico menzionato
2. Includi sia concetti generali che specifici
3. Normalizza i nomi (es. "tessuto epiteliale" non "tessuti epiteliali")
4. Escludi parole generiche come "introduzione", "cenni", "approfondimenti"
5. Ogni concetto deve essere una stringa di 2-5 parole massimo

Rispondi SOLO con un array JSON di stringhe, esempio:
["concetto 1", "concetto 2", "concetto 3"]

CONCETTI ESTRATTI:"""

        try:
            response_text = self._call_api(system_prompt, user_prompt)
            return self._parse_response(response_text)
        except Exception as e:
            print(f"[ERR] Errore {self.__class__.__name__}: {e}")
            return []
    
    def _parse_response(self, response_text: str) -> List[str]:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            cleaned = match.group()
        
        try:
            concepts = json.loads(cleaned)
            if isinstance(concepts, list):
                return [str(c).strip() for c in concepts if isinstance(c, str) and len(str(c).strip()) >= 3]
        except json.JSONDecodeError as e:
            print(f"[WARN] JSON parse error: {e}")
        
        return []
    
    @property
    def provider_name(self) -> str:
        return self.__class__.__name__.replace("Provider", "")


class OpenAIProvider(LLMProvider):
    """Provider per OpenAI"""
    
    AVAILABLE_MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    
    def _initialize_client(self):
        import openai
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content


class AnthropicProvider(LLMProvider):
    """Provider per Anthropic (Claude)"""
    
    AVAILABLE_MODELS = ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-3-5-20241022"]
    
    def _initialize_client(self):
        import anthropic
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return response.content[0].text


class GoogleProvider(LLMProvider):
    """Provider per Google (Gemini)"""
    
    AVAILABLE_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
    
    def _initialize_client(self):
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model)
    
    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self.client.generate_content(
            full_prompt,
            generation_config={"temperature": self.temperature, "max_output_tokens": self.max_tokens}
        )
        return response.text


class PerplexityProvider(LLMProvider):
    """Provider per Perplexity AI"""
    
    AVAILABLE_MODELS = ["llama-3.1-sonar-small-128k-online", "llama-3.1-sonar-large-128k-online", "llama-3.1-sonar-small-128k-chat", "llama-3.1-sonar-large-128k-chat"]
    
    def _initialize_client(self):
        import openai
        self.client = openai.OpenAI(api_key=self.api_key, base_url="https://api.perplexity.ai")
    
    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content


class ProviderRegistry:
    """Registry centrale dei provider disponibili"""
    
    PROVIDERS = {
        "openai": {
            "class": OpenAIProvider,
            "name": "OpenAI",
            "models": OpenAIProvider.AVAILABLE_MODELS,
            "default_model": "gpt-4o-mini",
            "key_env_var": "OPENAI_API_KEY",
            "key_label": "OpenAI API Key",
            "docs_url": "https://platform.openai.com/api-keys",
            "pricing_note": "gpt-4o-mini: ~$0.15/1M token"
        },
        "anthropic": {
            "class": AnthropicProvider,
            "name": "Anthropic (Claude)",
            "models": AnthropicProvider.AVAILABLE_MODELS,
            "default_model": "claude-sonnet-4-20250514",
            "key_env_var": "ANTHROPIC_API_KEY",
            "key_label": "Anthropic API Key",
            "docs_url": "https://console.anthropic.com/",
            "pricing_note": "Claude Sonnet: ~$3/1M token"
        },
        "google": {
            "class": GoogleProvider,
            "name": "Google (Gemini)",
            "models": GoogleProvider.AVAILABLE_MODELS,
            "default_model": "gemini-1.5-flash",
            "key_env_var": "GOOGLE_API_KEY",
            "key_label": "Google AI API Key",
            "docs_url": "https://aistudio.google.com/apikey",
            "pricing_note": "Gemini 1.5 Flash: gratuito fino 60 req/min"
        },
        "perplexity": {
            "class": PerplexityProvider,
            "name": "Perplexity AI",
            "models": PerplexityProvider.AVAILABLE_MODELS,
            "default_model": "llama-3.1-sonar-small-128k-chat",
            "key_env_var": "PERPLEXITY_API_KEY",
            "key_label": "Perplexity API Key",
            "docs_url": "https://www.perplexity.ai/settings/api",
            "pricing_note": "Sonar Small: ~$0.20/1M token"
        }
    }
    
    @classmethod
    def get_provider_names(cls) -> List[str]:
        return [p["name"] for p in cls.PROVIDERS.values()]
    
    @classmethod
    def get_provider_ids(cls) -> List[str]:
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def get_provider_info(cls, provider_id: str) -> Dict:
        return cls.PROVIDERS.get(provider_id, {})
    
    @classmethod
    def get_models_for_provider(cls, provider_id: str) -> List[str]:
        return cls.PROVIDERS.get(provider_id, {}).get("models", [])
    
    @classmethod
    def get_default_model(cls, provider_id: str) -> str:
        return cls.PROVIDERS.get(provider_id, {}).get("default_model", "")
    
    @classmethod
    def id_from_name(cls, name: str) -> str:
        for pid, info in cls.PROVIDERS.items():
            if info["name"] == name:
                return pid
        return "openai"


def create_provider(provider_id: str, api_key: str, model: Optional[str] = None) -> LLMProvider:
    """Factory per creare un provider"""
    if provider_id not in ProviderRegistry.PROVIDERS:
        raise ValueError(f"Provider '{provider_id}' non supportato")
    
    info = ProviderRegistry.PROVIDERS[provider_id]
    provider_class = info["class"]
    
    if model is None:
        model = info["default_model"]
    
    return provider_class(api_key=api_key, model=model)


def test_provider(provider_id: str, api_key: str, model: Optional[str] = None) -> Dict:
    """Testa la connessione a un provider"""
    try:
        provider = create_provider(provider_id, api_key, model)
        concepts = provider.extract_concepts("Termodinamica. Primo principio. Entropia.", "Fisica")
        return {
            "success": True,
            "provider": provider_id,
            "model": provider.model,
            "message": f"OK - Estratti {len(concepts)} concetti",
            "test_concepts": concepts
        }
    except Exception as e:
        return {"success": False, "provider": provider_id, "message": str(e), "test_concepts": []}


def get_provider_comparison() -> str:
    """Tabella comparativa per la UI"""
    lines = ["| Provider | Modello Default | Pricing |", "|----------|-----------------|---------|"]
    for info in ProviderRegistry.PROVIDERS.values():
        lines.append(f"| {info['name']} | {info['default_model']} | {info['pricing_note']} |")
    return "\n".join(lines)
