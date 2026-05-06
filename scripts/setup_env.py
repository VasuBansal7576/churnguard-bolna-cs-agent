"""Create backend and frontend env files from one guided prompt."""

from __future__ import annotations

import secrets
from getpass import getpass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ENV = ROOT / "backend" / ".env"
FRONTEND_ENV = ROOT / "frontend" / ".env.local"


def ask(label: str, *, secret: bool = False, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    prompt = f"{label}{suffix}: "
    value = getpass(prompt) if secret else input(prompt)
    return value.strip() or (default or "")


def write_env(path: Path, values: dict[str, str]) -> None:
    existing = path.read_text() if path.exists() else ""
    if existing.strip():
        backup = path.with_suffix(path.suffix + ".bak")
        backup.write_text(existing)
        print(f"Backed up existing {path.name} to {backup.name}")

    content = "\n".join(f"{key}={value}" for key, value in values.items()) + "\n"
    path.write_text(content)
    print(f"Wrote {path}")


def main() -> None:
    print("ChurnGuard local env setup")
    print("Paste credentials from Supabase and Bolna. Input is hidden for secrets.")
    print()

    supabase_url = ask("SUPABASE_URL")
    supabase_anon_key = ask("SUPABASE_ANON_KEY", secret=True)
    supabase_db_url = ask(
        "SUPABASE_DB_URL",
        secret=True,
        default="postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres",
    )
    bolna_api_key = ask("BOLNA_API_KEY", secret=True)
    bolna_agent_id = ask("BOLNA_AGENT_ID")
    admin_api_key = ask("ADMIN_API_KEY", secret=True, default=secrets.token_urlsafe(32))
    frontend_url = ask("FRONTEND_URL", default="http://localhost:3000")
    openai_api_key = ask("OPENAI_API_KEY", secret=True)
    backend_url = ask("NEXT_PUBLIC_BACKEND_URL", default="http://localhost:8000")

    write_env(
        BACKEND_ENV,
        {
            "SUPABASE_URL": supabase_url,
            "SUPABASE_ANON_KEY": supabase_anon_key,
            "SUPABASE_DB_URL": supabase_db_url,
            "BOLNA_API_KEY": bolna_api_key,
            "BOLNA_AGENT_ID": bolna_agent_id,
            "ADMIN_API_KEY": admin_api_key,
            "FRONTEND_URL": frontend_url,
            "OPENAI_API_KEY": openai_api_key,
        },
    )
    write_env(
        FRONTEND_ENV,
        {
            "NEXT_PUBLIC_SUPABASE_URL": supabase_url,
            "NEXT_PUBLIC_SUPABASE_ANON_KEY": supabase_anon_key,
            "NEXT_PUBLIC_BACKEND_URL": backend_url,
            "NEXT_PUBLIC_ADMIN_API_KEY": admin_api_key,
        },
    )

    print()
    print("Next: cd backend && alembic upgrade head")


if __name__ == "__main__":
    main()
