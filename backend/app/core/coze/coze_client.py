# src/coze/coze_client.py
import os

try:
    from cozepy import Coze
    COZE_AVAILABLE = True
except ImportError:
    COZE_AVAILABLE = False


class CozeClient:
    def __init__(self):
        self.api_token = os.environ.get("COZE_API_TOKEN", "")
        self.bot_id = os.environ.get("COZE_BOT_ID", "")
        self.client = None
        
        if COZE_AVAILABLE and self.api_token and self.bot_id:
            try:
                self.client = Coze(api_token=self.api_token)
            except Exception as e:
                print(f"Coze 初始化失败: {e}")

    def generate_rubrics(self, description: str) -> dict:
        if not self.client or not self.bot_id:
            return {"success": False, "error": "Coze 未配置", "rubrics": ""}

        try:
            response = self.client.bot.chat(
                bot_id=self.bot_id,
                user_id="teacher",
                content=f"请将以下描述转为评分规则JSON：{description}"
            )
            return {"rubrics": response.content, "success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "rubrics": ""}
