import logging
from typing import List, Dict, Optional

from app.core.config import config

# Optional imports; keep lazy to avoid hard dependency if provider not used
try:
	from openai import OpenAI as _OpenAIClient
except Exception:
	_OpenAIClient = None

try:
	import google.generativeai as genai
except Exception:
	genai = None


class AIResponse:
	class Choice:
		class Message:
			def __init__(self, content: str):
				self.content = content

		def __init__(self, content: str):
			self.message = AIResponse.Choice.Message(content)

	def __init__(self, content: str):
		self.choices = [AIResponse.Choice(content)]


class UnifiedAIClient:
	
	def __init__(self, provider: Optional[str] = None):
		self.provider = (provider or config.AI_PROVIDER).lower()

		if self.provider == "openai":
			if _OpenAIClient is None:
				raise RuntimeError("openai package is not available")
			self._client = _OpenAIClient(api_key=config.OPENAI_API_KEY)
		elif self.provider == "gemini":
			if genai is None:
				raise RuntimeError("google-generativeai package is not available")
			if not config.GEMINI_API_KEY:
				raise RuntimeError("GEMINI_API_KEY is not set")
			genai.configure(api_key=config.GEMINI_API_KEY)
			self._client = genai.GenerativeModel(config.GEMINI_MODEL)
		else:
			raise ValueError(f"Unsupported AI provider: {self.provider}")

	def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None,
			 temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> AIResponse:
		if self.provider == "openai":
			return self._chat_openai(messages, model or config.OPENAI_MODEL,
									 temperature if temperature is not None else config.OPENAI_TEMPERATURE,
									 max_tokens if max_tokens is not None else config.OPENAI_MAX_TOKENS)
		else:
			return self._chat_gemini(messages,
									 temperature if temperature is not None else config.GEMINI_TEMPERATURE,
									 max_tokens if max_tokens is not None else config.GEMINI_MAX_TOKENS)

	def _chat_openai(self, messages: List[Dict[str, str]], model: str, temperature: float, max_tokens: int) -> AIResponse:
		resp = self._client.chat.completions.create(
			messages=messages,
			model=model,
			temperature=temperature,
			max_tokens=max_tokens,
		)

		# normalize
		content = resp.choices[0].message.content
		return AIResponse(content)

	def _chat_gemini(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> AIResponse:
		logger = logging.getLogger(__name__)
		
		# Extract message parts
		system_parts = [m["content"] for m in messages if m.get("role") == "system"]
		user_parts = [m["content"] for m in messages if m.get("role") == "user"]
		assistant_parts = [m["content"] for m in messages if m.get("role") == "assistant"]

		# Compose prompt for Gemini
		system_text = "\n\n".join(system_parts) if system_parts else ""
		history = "\n".join([f"[ASSISTANT]\n{p}" for p in assistant_parts]) if assistant_parts else ""
		user_text = "\n".join(user_parts)
		prompt = "\n\n".join([p for p in [history, user_text] if p])

		gen_config = {
			"temperature": temperature,
			"max_output_tokens": max_tokens,
		}

		# Use system instruction if available
		model_for_call = self._client
		if system_text:
			try:
				model_for_call = genai.GenerativeModel(config.GEMINI_MODEL, system_instruction=system_text)  # type: ignore[arg-type]
			except Exception:
				model_for_call = self._client


		try:
			logger.debug(f"Calling Gemini API (model: {config.GEMINI_MODEL}, max_tokens: {max_tokens})")
			response = model_for_call.generate_content(
				prompt,
				generation_config=gen_config
			)
			logger.debug("Gemini API call completed successfully")

		except Exception as e:
			error_str = str(e)
			logger.error(f"Gemini API call failed: {e}", exc_info=True)
			return AIResponse("")
		
		try:
			content = response.text or ""
		except Exception:
			# Fallback for extracting  he response from each parts
			try:
				candidates = getattr(response, "candidates", None) or []
				text_parts = []
				for cand in candidates:
					parts = getattr(getattr(cand, "content", None), "parts", None) or []
					for p in parts:
						text_val = getattr(p, "text", None)
						if isinstance(text_val, str) and text_val.strip():
							text_parts.append(text_val.strip())
				content = "\n".join(text_parts).strip()
			except Exception:
				content = ""
		
		return AIResponse(content or "")


# Cached client instance for efficiency (reused across multiple calls)
_cached_client: Optional[UnifiedAIClient] = None


def ai_generate(messages: List[Dict[str, str]],
				model: Optional[str] = None,
				temperature: Optional[float] = None,
				max_tokens: Optional[int] = None) -> AIResponse:
	"""
	chat entry point.
	"""
	global _cached_client
	if _cached_client is None:
		_cached_client = UnifiedAIClient()
	return _cached_client.chat(messages=messages, model=model, temperature=temperature, max_tokens=max_tokens)


def count_tokens_provider(text: str) -> int:
	
	try:
		if config.AI_PROVIDER == "openai":
			import tiktoken
			enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
			return len(enc.encode(text))
		elif config.AI_PROVIDER == "gemini":
			if genai is None:
				raise RuntimeError("google-generativeai not installed")
			genai.configure(api_key=config.GEMINI_API_KEY)
			model = genai.GenerativeModel(config.GEMINI_MODEL)
			return int(model.count_tokens(text).total_tokens) 
	except Exception:
		pass
	# Heuristic fallback with ~4 chars per token
	return max(1, len(text) // 4)


def chunk_text_by_provider(text: str, max_tokens: int = 300) -> List[str]:

	# provider-native tokenizer path first
	if config.AI_PROVIDER == "openai":
		try:
			import tiktoken
			enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
			tokens = enc.encode(text)
			return [enc.decode(tokens[i:i + max_tokens]) for i in range(0, len(tokens), max_tokens)]
		except Exception:
			pass

	# Generic splitting by sentences/paragraphs with token budget
	chunks: List[str] = []
	current: List[str] = []
	current_tokens = 0

	parts = [p.strip() for p in text.split("\n") if p.strip()]
	sentences: List[str] = []
	for p in parts:
		sentences.extend([s.strip() for s in p.split(". ") if s.strip()])

	for s in sentences:
		tok = count_tokens_provider(s)
		if current_tokens + tok <= max_tokens or not current:
			current.append(s)
			current_tokens += tok
		else:
			chunks.append(". ".join(current).strip())
			current = [s]
			current_tokens = tok

	if current:
		chunks.append(". ".join(current).strip())

	return chunks


