from app.db import models
from app.utils import crud


def test_compute_effective_skills_fallback_to_base():
    player = models.PlayerScale5(
        name="Player",
        velocidad=2,
        resistencia=3,
        control=4,
        pases=5,
        tiro=1,
        defensa=2,
        habilidad_arquero=3,
        fuerza_cuerpo=4,
        vision=5,
    )

    effective, averages = crud.compute_effective_skills(player, [])

    assert effective["velocidad"] == 2
    assert averages["velocidad"] is None


def test_compute_effective_skills_with_votes():
    player = models.PlayerScale5(
        name="Player",
        velocidad=2,
        resistencia=3,
        control=4,
        pases=5,
        tiro=1,
        defensa=2,
        habilidad_arquero=3,
        fuerza_cuerpo=4,
        vision=5,
    )

    vote = models.SkillVote(
        club_id=1,
        voter_id=1,
        player_s5_id=1,
        velocidad=4,
        resistencia=4,
        control=4,
        pases=4,
        tiro=4,
        defensa=4,
        habilidad_arquero=4,
        fuerza_cuerpo=4,
        vision=4,
    )

    effective, averages = crud.compute_effective_skills(player, [vote])

    assert effective["velocidad"] == 4
    assert averages["velocidad"] == 4
