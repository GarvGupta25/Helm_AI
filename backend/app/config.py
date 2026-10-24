from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    app_env: str = "development"
    member_demo_auth: bool = False
    chatbot_feedback_database_url: str = ''
    database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres"
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_anon_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    groq_stt_model: str = "whisper-large-v3"
    send_real_emergency_alert: bool = False
    oncall_webhook_url: str = ""
    oncall_webhook_token: str = ""
    oncall_response_target_minutes: int = 15
    claim_confidence_threshold: float = 0.6
    claim_duplicate_threshold: float = 0.8
    claim_auto_approve_cap_aed: int = 10000
    document_encryption_key: str = ""
    research_state_key: str = ""
    research_llm_enabled: bool = False
    research_intent_model: str = "openai/gpt-oss-20b"
    otp_delivery_mode: str = 'console'
    otp_allowlist: list[str] = []
    whatsapp_access_token: str = ''
    whatsapp_phone_number_id: str = ''
    whatsapp_graph_version: str = ''
    whatsapp_auth_template: str = ''
    whatsapp_utility_template: str = ''
    public_quote_origin: str = ''
    broker_notification_destination: str = ''
    broker_notification_channel: str = 'email'
    whatsapp_template_language: str = 'en'
    smtp_host: str = ''
    smtp_port: int = 465
    smtp_user: str = ''
    smtp_password: str = ''
    smtp_from: str = ''
    public_upload_ttl_seconds: int = 86400
    payment_provider: str = "simulator"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4174", "http://127.0.0.1:4174", "http://localhost:4175", "http://127.0.0.1:4175"]
    tesseract_cmd: str = ""


@lru_cache
def settings():
    return Settings()
