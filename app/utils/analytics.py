from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Connection


def _week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _as_date(value) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _build_daily_series(raw_counts: dict[date, int], days: int) -> list[dict]:
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    result = []

    for offset in range(days):
        current_day = start_date + timedelta(days=offset)
        result.append(
            {
                "date": current_day.isoformat(),
                "count": int(raw_counts.get(current_day, 0)),
            }
        )

    return result


def get_daily_new_users(conn: Connection, days: int) -> list[dict]:
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    rows = conn.execute(
        text(
            """
            SELECT DATE(created_at) AS day, COUNT(*) AS count
            FROM users
            WHERE DATE(created_at) BETWEEN :start_date AND :end_date
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
            """
        ),
        {"start_date": start_date, "end_date": today},
    ).fetchall()

    raw_counts = {_as_date(row.day): int(row.count) for row in rows}
    return _build_daily_series(raw_counts, days)


def get_daily_new_clubs(conn: Connection, days: int) -> list[dict]:
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    rows = conn.execute(
        text(
            """
            SELECT DATE(creation_date) AS day, COUNT(*) AS count
            FROM clubs
            WHERE DATE(creation_date) BETWEEN :start_date AND :end_date
            GROUP BY DATE(creation_date)
            ORDER BY DATE(creation_date)
            """
        ),
        {"start_date": start_date, "end_date": today},
    ).fetchall()

    raw_counts = {_as_date(row.day): int(row.count) for row in rows}
    return _build_daily_series(raw_counts, days)


def get_weekly_cohort_retention(conn: Connection, num_cohorts: int = 4) -> list[dict]:
    current_week_start = _week_start(date.today())
    oldest_cohort_start = current_week_start - timedelta(weeks=num_cohorts - 1)
    next_week_start = current_week_start + timedelta(weeks=1)

    rows = conn.execute(
        text(
            """
            SELECT
                DATE_TRUNC('week', u.created_at)::date AS cohort_week_start,
                COUNT(*) AS cohort_size,
                COUNT(u.id) FILTER (WHERE u.last_seen_at >= :current_week_start) AS retained_count
            FROM users u
            WHERE u.created_at >= :oldest_cohort_start
              AND u.created_at < :next_week_start
            GROUP BY DATE_TRUNC('week', u.created_at)::date
            ORDER BY cohort_week_start
            """
        ),
        {
            "current_week_start": current_week_start,
            "oldest_cohort_start": oldest_cohort_start,
            "next_week_start": next_week_start,
        },
    ).fetchall()

    rows_by_week = {
        _as_date(row.cohort_week_start): {
            "cohort_size": int(row.cohort_size),
            "retained_count": int(row.retained_count),
        }
        for row in rows
    }

    result = []
    for index in range(num_cohorts):
        week_start = oldest_cohort_start + timedelta(weeks=index)
        cohort_data = rows_by_week.get(
            week_start, {"cohort_size": 0, "retained_count": 0}
        )
        cohort_size = cohort_data["cohort_size"]
        retained_count = cohort_data["retained_count"]
        retention_rate = (
            round((retained_count / cohort_size) * 100, 1) if cohort_size > 0 else 0.0
        )
        result.append(
            {
                "cohort_week_start": week_start.isoformat(),
                "cohort_size": cohort_size,
                "retained_count": retained_count,
                "retention_rate": retention_rate,
            }
        )

    return result


def get_weekly_matches_created(conn: Connection, weeks: int = 8) -> list[dict]:
    current_week_start = _week_start(date.today())
    oldest_week_start = current_week_start - timedelta(weeks=weeks - 1)
    next_week_start = current_week_start + timedelta(weeks=1)

    rows = conn.execute(
        text(
            """
            SELECT
                DATE_TRUNC('week', created_at)::date AS week_start,
                COUNT(*) FILTER (WHERE club_id IS NOT NULL) AS club_matches,
                COUNT(*) FILTER (WHERE club_id IS NULL) AS individual_matches
            FROM matches
            WHERE created_at >= :oldest_week_start
              AND created_at < :next_week_start
            GROUP BY DATE_TRUNC('week', created_at)::date
            ORDER BY week_start
            """
        ),
        {"oldest_week_start": oldest_week_start, "next_week_start": next_week_start},
    ).fetchall()

    rows_by_week = {
        _as_date(row.week_start): {
            "club_matches": int(row.club_matches),
            "individual_matches": int(row.individual_matches),
        }
        for row in rows
    }

    result = []
    for index in range(weeks):
        week_start = oldest_week_start + timedelta(weeks=index)
        week_data = rows_by_week.get(
            week_start, {"club_matches": 0, "individual_matches": 0}
        )
        result.append(
            {
                "week_start": week_start.isoformat(),
                "club_matches": week_data["club_matches"],
                "individual_matches": week_data["individual_matches"],
            }
        )

    return result


def get_match_creator_stats(conn: Connection) -> dict:
    row = conn.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_matches,
                COUNT(DISTINCT created_by) AS distinct_creators
            FROM matches
            """
        )
    ).one()
    return {
        "total_matches": int(row.total_matches),
        "distinct_creators": int(row.distinct_creators),
    }


def get_shared_profile_stats(conn: Connection) -> dict:
    row = conn.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_shared_links,
                COUNT(DISTINCT user_id) AS distinct_sharing_users
            FROM (
                SELECT user_id FROM players_s5 WHERE share_token IS NOT NULL
                UNION ALL
                SELECT user_id FROM players_s10 WHERE share_token IS NOT NULL
            ) AS shared_players
            """
        )
    ).one()
    return {
        "total_shared_links": int(row.total_shared_links),
        "distinct_sharing_users": int(row.distinct_sharing_users),
    }


def get_player_photo_stats(conn: Connection) -> dict:
    row = conn.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_players_with_photo,
                COUNT(DISTINCT user_id) AS distinct_users_with_photo
            FROM (
                SELECT user_id FROM players_s5
                WHERE photo_url IS NOT NULL AND photo_url != ''
                UNION ALL
                SELECT user_id FROM players_s10
                WHERE photo_url IS NOT NULL AND photo_url != ''
            ) AS players_with_photo
            """
        )
    ).one()
    return {
        "total_players_with_photo": int(row.total_players_with_photo),
        "distinct_users_with_photo": int(row.distinct_users_with_photo),
    }


def get_skill_vote_stats(conn: Connection) -> dict:
    row = conn.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_votes,
                COUNT(DISTINCT club_id) AS distinct_clubs_with_votes,
                COUNT(DISTINCT voter_id) AS distinct_voters
            FROM skill_votes
            """
        )
    ).one()
    return {
        "total_votes": int(row.total_votes),
        "distinct_clubs_with_votes": int(row.distinct_clubs_with_votes),
        "distinct_voters": int(row.distinct_voters),
    }
