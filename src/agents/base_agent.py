"""Base Agent class for multi-agent trading system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass
import aiohttp
import json
from loguru import logger


@dataclass
class AgentOpinion:
    """Opinion from a trading agent."""
    agent_name: str
    stance: str  # "BULLISH", "BEARISH", "NEUTRAL"
    confidence: float  # 0.0-1.0
    reasoning: str
    key_points: List[str]
    suggested_action: str  # "BUY", "SELL", "HOLD"


class BaseAgent(ABC):
    """Base class for all trading agents."""

    def __init__(self, name: str, role: str, api_key: str, model: str = "deepseek-chat"):
        """
        Initialize agent.

        Args:
            name: Agent's name
            role: Agent's role/expertise
            api_key: DeepSeek API key
            model: Model to use
        """
        self.name = name
        self.role = role
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com"

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    async def analyze(self,
                     context: Dict[str, Any],
                     discussion_history: List[AgentOpinion] = None) -> AgentOpinion:
        """
        Analyze market data and provide opinion.

        Args:
            context: Market data and indicators
            discussion_history: Previous agents' opinions

        Returns:
            Agent's opinion
        """
        # Build prompt with context
        prompt = self._build_prompt(context, discussion_history)

        # Get response from DeepSeek
        response = await self._call_deepseek(prompt)

        # Parse response
        opinion = self._parse_response(response)

        return opinion

    def _build_prompt(self, context: Dict[str, Any], discussion_history: List[AgentOpinion] = None) -> str:
        """Build prompt with context and discussion history."""
        prompt = f"# Market Context\n"
        prompt += f"Asset: {context.get('asset', 'Unknown')}\n"
        prompt += f"Price: ${context.get('price', 0):.2f}\n\n"

        # Add indicators if available
        if 'indicators' in context:
            ind = context['indicators']
            prompt += "# Technical Indicators\n"
            prompt += f"RSI: {ind.get('rsi', 'N/A')}\n"
            prompt += f"ADX: {ind.get('adx', 'N/A')}\n"
            prompt += f"MACD: {ind.get('macd', 'N/A')}\n\n"

        # Add discussion history
        if discussion_history:
            prompt += "# Trading Desk Discussion\n"
            for opinion in discussion_history:
                prompt += f"\n**{opinion.agent_name}** ({opinion.stance}):\n"
                prompt += f"{opinion.reasoning}\n"
            prompt += "\n"

        prompt += "# Your Analysis\n"
        prompt += "Provide your expert opinion in this format:\n"
        prompt += "{\n"
        prompt += '  "stance": "BULLISH|BEARISH|NEUTRAL",\n'
        prompt += '  "confidence": 0.0-1.0,\n'
        prompt += '  "reasoning": "Your detailed reasoning",\n'
        prompt += '  "key_points": ["Point 1", "Point 2", "Point 3"],\n'
        prompt += '  "suggested_action": "BUY|SELL|HOLD"\n'
        prompt += "}\n"

        return prompt

    async def _call_deepseek(self, user_prompt: str) -> Dict[str, Any]:
        """Call DeepSeek API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.get_system_prompt()},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 800
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]

                        # Try to parse JSON from response
                        try:
                            # Find JSON in response
                            start = content.find("{")
                            end = content.rfind("}") + 1
                            if start != -1 and end > start:
                                json_str = content[start:end]
                                return json.loads(json_str)
                        except:
                            pass

                        # Fallback: return raw content
                        return {"reasoning": content, "stance": "NEUTRAL", "confidence": 0.5}
                    else:
                        logger.error(f"{self.name}: API error {response.status}")
                        return {"reasoning": "API error", "stance": "NEUTRAL", "confidence": 0.0}

        except Exception as e:
            logger.error(f"{self.name}: Error calling DeepSeek: {e}")
            return {"reasoning": f"Error: {str(e)}", "stance": "NEUTRAL", "confidence": 0.0}

    def _parse_response(self, response: Dict[str, Any]) -> AgentOpinion:
        """Parse DeepSeek response into AgentOpinion."""
        return AgentOpinion(
            agent_name=self.name,
            stance=response.get("stance", "NEUTRAL"),
            confidence=float(response.get("confidence", 0.5)),
            reasoning=response.get("reasoning", ""),
            key_points=response.get("key_points", []),
            suggested_action=response.get("suggested_action", "HOLD")
        )
