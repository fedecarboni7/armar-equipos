#!/usr/bin/env python3
"""
Script simple para crear 10 jugadores de ejemplo para testing.
Ubicado en tests/utils/ para mantener organizado el proyecto.
"""

import random
import sys
import os

# Agregar la raíz del proyecto al sys.path de forma robusta
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.db.database import SessionLocal, engine  # noqa: E402
from app.db.models import User, Player, Base  # noqa: E402


def create_sample_players(username: str):
    """Crea 10 jugadores de ejemplo para el usuario especificado."""

    # Crear las tablas si no existen
    Base.metadata.create_all(bind=engine)

    # Obtener una sesión de base de datos
    db = SessionLocal()

    try:
        # Buscar el usuario especificado
        user = db.query(User).filter(User.username == username).first()

        if not user:
            print(f"Usuario '{username}' no encontrado.")
            return False
        else:
            print(f"Usuario '{username}' encontrado con ID: {user.id}")

        # Lista de nombres de jugadores
        player_names = [
            "Lionel Messi",
            "Cristiano Ronaldo",
            "Kylian Mbappé",
            "Erling Haaland",
            "Kevin De Bruyne",
            "Virgil van Dijk",
            "Neymar Jr",
            "Robert Lewandowski",
            "Luka Modrić",
            "Mohamed Salah",
        ]

        # Verificar si ya existen jugadores para este usuario
        existing_players = db.query(Player).filter(Player.user_id == user.id).count()
        print(f"Jugadores existentes para usuario '{username}': {existing_players}")

        if existing_players > 0:
            response = input("¿Querés eliminar los jugadores existentes? (y/n): ")
            if response.lower() == "y":
                db.query(Player).filter(Player.user_id == user.id).delete()
                db.commit()
                print("Jugadores existentes eliminados.")

        # Crear 10 jugadores
        created_players = []
        for i, name in enumerate(player_names):
            player = Player(
                name=name,
                velocidad=random.randint(1, 5),
                resistencia=random.randint(1, 5),
                control=random.randint(1, 5),
                pases=random.randint(1, 5),
                tiro=random.randint(1, 5),
                defensa=random.randint(1, 5),
                habilidad_arquero=random.randint(1, 5),
                fuerza_cuerpo=random.randint(1, 5),
                vision=random.randint(1, 5),
                user_id=user.id,
                club_id=None,  # Sin club por defecto
            )

            db.add(player)
            created_players.append(player)

        # Guardar todos los jugadores en la base de datos
        db.commit()

        print(
            f"\n✅ Se han creado {len(created_players)} jugadores para el usuario '{username}':"
        )
        print("-" * 60)

        for player in created_players:
            db.refresh(player)  # Refrescar para obtener el ID
            print(
                f"ID: {player.id:2d} | {player.name:18s} | "
                f"Vel:{player.velocidad} Res:{player.resistencia} Con:{player.control} "
                f"Pas:{player.pases} Tir:{player.tiro} Def:{player.defensa} "
                f"Arq:{player.habilidad_arquero} Fue:{player.fuerza_cuerpo} Vis:{player.vision}"
            )

        print("-" * 60)
        print("🎉 ¡Jugadores creados exitosamente!")
        return True

    except Exception as e:
        print(f"❌ Error al crear jugadores: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    username = input("Introduce el nombre de usuario: ")
    print(f"⚽ Creando jugadores de ejemplo para el usuario '{username}'...")
    create_sample_players(username)
