"""Criação das tabelas iniciais (6 entidades do DER — Seção 7).

Revision ID: 0001_initial
Revises: None
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("email", sa.String(150), nullable=False, unique=True),
        sa.Column("senha", sa.String(255), nullable=False),
        sa.Column("perfil", sa.String(50), nullable=False, server_default="participante"),
        sa.Column("data_cadastro", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
    )
    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(100), nullable=False, unique=True),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
    )
    op.create_table(
        "eventos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(200), nullable=False),  # DER: "nome"
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("data_evento", sa.Date(), nullable=False),
        sa.Column("horario", sa.Time(), nullable=True),
        sa.Column("local", sa.String(200), nullable=True),
        sa.Column("capacidade", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categorias.id"), nullable=False),
        sa.Column("organizador_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
    )
    op.create_table(
        "inscricoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("evento_id", sa.Integer(), sa.ForeignKey("eventos.id"), nullable=False),
        sa.Column("data_inscricao", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ativa"),
        sa.UniqueConstraint("usuario_id", "evento_id", name="uq_inscricao_usuario_evento"),
    )
    op.create_table(
        "certificados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("inscricao_id", sa.Integer(), sa.ForeignKey("inscricoes.id"), nullable=False, unique=True),
        sa.Column("codigo_validacao", sa.String(50), nullable=False, unique=True),
        sa.Column("data_emissao", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="emitido"),
    )
    op.create_table(
        "favoritos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("evento_id", sa.Integer(), sa.ForeignKey("eventos.id"), nullable=False),
        sa.Column("data_favorito", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("usuario_id", "evento_id", name="uq_favorito_usuario_evento"),
    )


def downgrade() -> None:
    op.drop_table("favoritos")
    op.drop_table("certificados")
    op.drop_table("inscricoes")
    op.drop_table("eventos")
    op.drop_table("categorias")
    op.drop_table("usuarios")
