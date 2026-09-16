from datetime import date

from app.db import models


def _get_test_user(db):
    return db.query(models.User).filter(models.User.username == "testuser").first()


def _player_kwargs(name, user_id, club_id):
    return dict(
        name=name,
        velocidad=5,
        resistencia=5,
        control=5,
        pases=5,
        tiro=5,
        defensa=5,
        habilidad_arquero=5,
        fuerza_cuerpo=5,
        vision=5,
        user_id=user_id,
        club_id=club_id,
    )


def test_delete_club_with_matches_cascades(authenticated_client, db):
    user = _get_test_user(db)
    club = models.Club(name="Club To Delete")
    db.add(club)
    db.flush()
    db.add(models.ClubUser(club_id=club.id, user_id=user.id, role="owner"))

    player_s5 = models.PlayerScale5(**_player_kwargs("S5 Player", user.id, club.id))
    player_s10 = models.PlayerScale10(**_player_kwargs("S10 Player", user.id, club.id))
    db.add_all([player_s5, player_s10])
    db.commit()
    db.refresh(player_s5)
    db.refresh(player_s10)

    match = models.Match(
        club_id=club.id,
        created_by=user.id,
        played_at=date(2026, 5, 20),
        team_a_score=1,
        team_b_score=1,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    match_id = match.id

    db.add_all(
        [
            models.MatchPlayer(
                match_id=match_id,
                player_s5_id=player_s5.id,
                player_s10_id=None,
                team="A",
                result="draw",
            ),
            models.MatchPlayer(
                match_id=match_id,
                player_s5_id=None,
                player_s10_id=player_s10.id,
                team="B",
                result="draw",
            ),
            models.SkillVote(
                club_id=club.id,
                voter_id=user.id,
                player_s5_id=player_s5.id,
                player_s10_id=None,
                **{
                    field: 5
                    for field in (
                        "velocidad",
                        "resistencia",
                        "control",
                        "pases",
                        "tiro",
                        "defensa",
                        "habilidad_arquero",
                        "fuerza_cuerpo",
                        "vision",
                    )
                },
            ),
        ]
    )
    db.commit()
    club_id = club.id

    response = authenticated_client.delete(f"/clubs/{club_id}")

    assert response.status_code == 200
    assert response.json()["id"] == club_id
    assert db.query(models.Club).filter_by(id=club_id).first() is None
    assert db.query(models.Match).filter_by(club_id=club_id).count() == 0
    assert db.query(models.MatchPlayer).filter_by(match_id=match_id).count() == 0
    assert db.query(models.SkillVote).filter_by(club_id=club_id).count() == 0
    assert db.query(models.PlayerScale5).filter_by(club_id=club_id).count() == 0
    assert db.query(models.PlayerScale10).filter_by(club_id=club_id).count() == 0
    assert db.query(models.ClubUser).filter_by(club_id=club_id).count() == 0


def test_delete_club_not_found(authenticated_client, db):
    response = authenticated_client.delete("/clubs/999999999")
    assert response.status_code == 404


def test_delete_club_forbidden_for_non_owner(authenticated_client, db):
    user = _get_test_user(db)
    club = models.Club(name="Not Owned Club")
    db.add(club)
    db.flush()
    db.add(models.ClubUser(club_id=club.id, user_id=user.id, role="member"))
    db.commit()
    club_id = club.id

    response = authenticated_client.delete(f"/clubs/{club_id}")

    assert response.status_code == 403
    assert db.query(models.Club).filter_by(id=club_id).first() is not None
