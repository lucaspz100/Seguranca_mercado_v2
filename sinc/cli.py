"""CLI de administração do SINC.

Uso:
    python -m sinc.cli create-admin --email admin@sinc.local --username admin --password SincAdmin123
    sinc create-admin ...  (se instalado via pip)
"""

import asyncio

import typer
from passlib.context import CryptContext
from sqlalchemy import select

from sinc.db.session import AsyncSessionLocal
from sinc.models.audit_log import AuditLog
from sinc.models.user import User
from sinc.schemas.common import Role

app = typer.Typer(help="Comandos de administração do SINC")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


@app.command()
def create_admin(
    email: str = typer.Option(..., prompt=True, help="Email do administrador"),
    username: str = typer.Option(..., prompt=True, help="Nome de usuário"),
    password: str = typer.Option(
        ..., prompt=True, hide_input=True, confirmation_prompt=True, help="Senha"
    ),
    force: bool = typer.Option(False, "--force", help="Permite criar segundo admin"),
) -> None:
    """Cria um usuário ADMIN no banco. Usar apenas na configuração inicial."""
    asyncio.run(_create_admin(email, username, password, force))


async def _create_admin(email: str, username: str, password: str, force: bool) -> None:
    async with AsyncSessionLocal() as db:
        if not force:
            result = await db.execute(
                select(User).where(User.role == Role.ADMIN.value)
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                typer.echo(
                    f"Já existe um admin ({existing.email}). Use --force para criar outro.",
                    err=True,
                )
                raise typer.Exit(code=1)

        hashed = pwd_context.hash(password)
        user = User(
            email=email,
            username=username,
            hashed_password=hashed,
            role=Role.ADMIN.value,
        )
        db.add(user)
        await db.flush()

        db.add(
            AuditLog(
                user_id=user.id,
                action="admin.created_via_cli",
                resource_type="user",
                resource_id=str(user.id),
                details={"email": email, "username": username},
            )
        )
        await db.commit()

    typer.echo(f"Admin criado com sucesso: {email} (username: {username})")


if __name__ == "__main__":
    app()
