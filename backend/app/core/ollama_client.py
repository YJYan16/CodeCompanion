"""
Ollama客户端 - 用于本地模型推理
支持Qwen2.5等本地模型，实现离线批改功能
"""
import httpx
import json
from typing import Optional, Dict, List, Any
import asyncio


class OllamaClient:
    """Ollama本地模型客户端"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:0.5b"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = 300.0  # 5分钟超时
    
    async def _check_connection(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    async def _check_model(self) -> bool:
        """检查模型是否已下载"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get('models', [])
                    return any(model.get('name', '').startswith(self.model.split(':')[0]) for model in models)
        except Exception:
            pass
        return False
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            生成的文本
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                
                if stream:
                    # 流式输出处理
                    full_text = ""
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                full_text += data.get('response', '')
                            except json.JSONDecodeError:
                                pass
                    return full_text
                else:
                    # 非流式输出
                    data = response.json()
                    return data.get('response', '')
        except httpx.TimeoutException:
            raise Exception(f"Ollama请求超时（{self.timeout}秒），请检查模型是否正常运行")
        except httpx.HTTPError as e:
            raise Exception(f"Ollama请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"Ollama生成失败: {str(e)}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """
        对话生成
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            生成的回复
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                
                if stream:
                    # 流式输出处理
                    full_text = ""
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if 'message' in data:
                                    full_text += data['message'].get('content', '')
                            except json.JSONDecodeError:
                                pass
                    return full_text
                else:
                    # 非流式输出
                    data = response.json()
                    return data.get('message', {}).get('content', '')
        except httpx.TimeoutException:
            raise Exception(f"Ollama请求超时（{self.timeout}秒），请检查模型是否正常运行")
        except httpx.HTTPError as e:
            raise Exception(f"Ollama请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"Ollama对话失败: {str(e)}")
    
    async def get_status(self) -> Dict[str, Any]:
        """
        获取Ollama服务状态
        
        Returns:
            状态信息字典
        """
        status = {
            "connected": False,
            "model_available": False,
            "model_name": self.model,
            "error": None
        }
        
        try:
            status["connected"] = await self._check_connection()
            if status["connected"]:
                status["model_available"] = await self._check_model()
        except Exception as e:
            status["error"] = str(e)
        
        return status
    
    async def pull_model(self) -> bool:
        """
        拉取模型（如果未下载）
        
        Returns:
            是否成功
        """
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": self.model, "stream": False}
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"拉取模型失败: {str(e)}")
            return False


# 创建全局Ollama客户端实例
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> Optional[OllamaClient]:
    """获取Ollama客户端单例"""
    global _ollama_client
    if _ollama_client is None:
        from config.settings import get_settings
        settings = get_settings()
        _ollama_client = OllamaClient(
            base_url=settings.local_model_url.replace('/api/generate', ''),
            model=settings.local_model_name
        )
    return _ollama_client