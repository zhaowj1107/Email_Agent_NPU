import os
from pydantic import BaseModel, Field

class Settings(BaseModel):
    # Email configuration
    email_address: str = Field(..., env="EMAIL_ADDRESS")
    email_password: str = Field(..., env="EMAIL_PASSWORD")
    imap_server: str = Field(default="imap.gmail.com")
    
    # Processing settings
    check_interval: int = Field(default=60)
    max_email_size: int = Field(default=10485760)  # 10MB
    
    # Notification settings
    whatsapp_enabled: bool = Field(default=False)
    wechat_enabled: bool = Field(default=False)
    
    # Calendar integration
    calendar_type: str = Field(default="google")
    
    # LLM settings
    llm_model_path: str = Field(default="models/llama-2-7b-chat.Q4_K_M.gguf")
    rag_index_path: str = Field(default="data/rag_index")

    @classmethod
    def from_env(cls):
        return cls(
            email_address=os.getenv("EMAIL_ADDRESS"),
            email_password=os.getenv("EMAIL_PASSWORD"),
            imap_server=os.getenv("IMAP_SERVER", "imap.gmail.com"),
            check_interval=int(os.getenv("CHECK_INTERVAL", "60")),
            max_email_size=int(os.getenv("MAX_EMAIL_SIZE", "10485760")),
            whatsapp_enabled=bool(os.getenv("WHATSAPP_ENABLED", "False")),
            wechat_enabled=bool(os.getenv("WECHAT_ENABLED", "False")),
            calendar_type=os.getenv("CALENDAR_TYPE", "google"),
            llm_model_path=os.getenv("LLM_MODEL_PATH", "models/llama-2-7b-chat.Q4_K_M.gguf"),
            rag_index_path=os.getenv("RAG_INDEX_PATH", "data/rag_index")
        )

settings = Settings.from_env()
