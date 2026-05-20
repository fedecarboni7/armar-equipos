# DATABASE.md — Armar Equipos

Schema de la base de datos generado a partir de `app/db/models.py`.

> Todos los timestamps usan timezone de Argentina (America/Buenos_Aires).

---

## Tablas

- [users](#users)
- [players](#players)
- [players_v2](#players_v2)
- [skill_votes](#skill_votes)
- [skill_votes_v2](#skill_votes_v2)
- [clubs](#clubs)
- [club_users](#club_users)
- [club_invitations](#club_invitations)
- [password_reset_tokens](#password_reset_tokens)
- [matches](#matches)
- [match_players](#match_players)

---

## users

Usuarios registrados en la aplicación.

| Columna | Tipo | Constraints | Descripción |
|---|---|---|---|
| id | Integer | PK, indexed | Identificador único del usuario |
| username | String | UNIQUE, indexed, NOT NULL | Nombre de usuario para login |
| password | String | NOT NULL | Hash de la contraseña (pbkdf2_sha256) |
| email | String | UNIQUE, indexed, NULLABLE | Email del usuario. Nullable para usuarios legacy |
| email_confirmed | Integer | NOT NULL, DEFAULT 0 | Estado de confirmación: `0`=nuevo sin confirmar, `-1`=legacy sin confirmar, `1`=confirmado |
| email_confirmation_token | String | NULLABLE | Token para confirmar el email |
| email_confirmation_expires | DateTime | NULLABLE | Expiración del token de confirmación |
| created_at | DateTime | DEFAULT now() | Fecha de registro |

### Relationships

| Relación | Tipo | Descripción |
|---|---|---|
| `players` | one-to-many → `players` | Jugadores creados por este usuario |
| `players_v2` | one-to-many → `players_v2` | Jugadores creados por este usuario |
| `skill_votes` | one-to-many → `skill_votes` | Votos de habilidades emitidos por este usuario |
| `skill_votes_v2` | one-to-many → `skill_votes_v2` | Votos de habilidades emitidos por este usuario |
| `club_users` | one-to-many → `club_users` | Membresías a clubes |

---

## players

Jugadores del sistema (puntuación de habilidades del 1 al 5).

| Columna | Tipo | Constraints | Descripción |
|---|---|---|---|
| id | Integer | PK, indexed | Identificador único del jugador |
| name | String | indexed | Nombre del jugador |
| velocidad | Integer | | Habilidad: velocidad |
| resistencia | Integer | | Habilidad: resistencia |
| control | Integer | | Habilidad: control de balón |
| pases | Integer | | Habilidad: pases |
| tiro | Integer | | Habilidad: tiro |
| defensa | Integer | | Habilidad: defensa |
| habilidad_arquero | Integer | | Habilidad: arquero |
| fuerza_cuerpo | Integer | | Habilidad: fuerza corporal |
| vision | Integer | | Habilidad: visión de juego |
| photo_data | Text | NULLABLE | Foto del jugador en Base64 |
| user_id | Integer | FK → users.id | Usuario propietario del jugador |
| club_id | Integer | FK → clubs.id | Club al que pertenece el jugador |
| updated_at | DateTime | DEFAULT/UPDATE now() | Última actualización del perfil |
| last_modified_by | Integer | FK → users.id, NULLABLE | Usuario que realizó la última modificación |

### Relationships

| Relación | Tipo | Descripción |
|---|---|---|
| `user` | many-to-one → `users` | Propietario del jugador |
| `last_modifier` | many-to-one → `users` | Último usuario que modificó el jugador |
| `club` | many-to-one → `clubs` | Club del jugador |
| `skill_votes` | one-to-many → `skill_votes` | Votos recibidos sobre las habilidades de este jugador |

---

## players_v2

Jugadores del sistema (puntuación de habilidades del 1 al 10). Misma estructura que `players`.

| Columna | Tipo | Constraints | Descripción |
|---|---|---|---|
| id | Integer | PK, indexed | Identificador único del jugador |
| name | String | indexed | Nombre del jugador |
| velocidad | Integer | | Habilidad: velocidad |
| resistencia | Integer | | Habilidad: resistencia |
| control | Integer | | Habilidad: control de balón |
| pases | Integer | | Habilidad: pases |
| tiro | Integer | | Habilidad: tiro |
| defensa | Integer | | Habilidad: defensa |
| habilidad_arquero | Integer | | Habilidad: arquero |
| fuerza_cuerpo | Integer | | Habilidad: fuerza corporal |
| vision | Integer | | Habilidad: visión de juego |
| photo_data | Text | NULLABLE | Foto del jugador en Base64 |
| user_id | Integer | FK → users.id | Usuario propietario del jugador |
| club_id | Integer | FK → clubs.id | Club al que pertenece el jugador |
| updated_at | DateTime | DEFAULT/UPDATE now() | Última actualización del perfil |
| last_modified_by | Integer | FK → users.id, NULLABLE | Usuario que realizó la última modificación |

### Relationships

| Relación | Tipo | Descripción |
|---|---|---|
| `user` | many-to-one → `users` | Propietario del jugador |
| `last_modifier` | many-to-one → `users` | Último usuario que modificó el jugador |
| `club` | many-to-one → `clubs` | Club del jugador |
| `skill_votes_v2` | one-to-many → `skill_votes_v2` | Votos recibidos sobre las habilidades de este jugador |

---

## skill_votes

Votos de habilidades sobre jugadores de tabla `players` (por ahora sin uso).

| Columna | Tipo | Constraints | Descripción |
|---|---|---|---|
| id | Integer | PK, indexed | Identificador único del voto |
| player_id | Integer | FK → players.id | Jugador evaluado |
| voter_id | Integer | FK → users.id | Usuario que emitió el voto |
| velocidad | Integer | | Puntuación: velocidad |
| resistencia | Integer | | Puntuación: resistencia |
| control | Integer | | Puntuación: control de balón |
| pases | Integer | | Puntuación: pases |
| tiro | Integer | | Puntuación: tiro |
| defensa | Integer | | Puntuación: defensa |
| habilidad_arquero | Integer | | Puntuación: arquero |
| fuerza_cuerpo | Integer | | Puntuación: fuerza corporal |
| vision | Integer | | Puntuación: visión de juego |
| vote_date | DateTime | DEFAULT now() | Fecha en que se emitió el voto |

### Relationships

| Relación | Tipo | Descripción |
|---|---|---|
| `player` | many-to-one → `players` | Jugador evaluado |
| `voter` | many-to-one → `users` | Usuario que votó |

---

## skill_votes_v2

Votos de habilidades sobre jugadores de tabla `players_v2` (por ahora sin uso).

| Columna | Tipo | Constraints | Descripción |
|---|---|---|---|
| id | Integer | PK, indexed | Identificador único del voto |
| player_id | Integer | FK → players_v2.id | Jugador evaluado |
| voter_id | Integer | FK → users.id | Usuario que emitió el voto |
| velocidad | Integer | | Puntuación: velocidad |
| resistencia | Integer | | Puntuación: resistencia |
| control | Integer | | Puntuación: control de balón |
| pases | Integer | | Puntuación: pases |
| tiro | Integer | | Puntuación: tiro |
| defensa | Integer | | Puntuación: defensa |
| habilidad_arquero | Integer | | Puntuación: arquero |
| fuerza_cuerpo | Integer | | Puntuación: fuerza corporal |
| vision | Integer | | Puntuación: visión de juego |
| vote_date | DateTime | DEFAULT now() | Fecha en que se emitió el voto |

### Relationships

| Relación | Tipo | Descripción |
|---|---|---|
| `player` | many-to-one → `players_v2` | Jugador evaluado |
| `voter` | many-to-one → `users` | Usuario que votó |

---

## clubs

Clubes o grupos de jugadores.

| Columna | Tipo | Constraints | Descripción |
|---|---|---|---|
| id | Integer | PK, indexed | Identificador único del club |
| name | String | | Nombre del club |
| creation_date | DateTime | DEFAULT now() | Fecha de creación del club |

### Relationships

| Relación | Tipo | Descripción |
|---|---|---|
| `members` | one-to-many → `club_users` | Miembros del club |
| `players` | one-to-many → `players` | Jugadores del club (1-5) |
| `players_v2` | one-to-many → `players_v2` | Jugadores del club (1-10) |
| `invitations` | one-to-many → `club_invitations` | Invitaciones emitidas por este club |

---

## club_users

Tabla de membresía que relaciona usuarios con clubes, incluyendo su rol.

| Columna | Tipo | Constraints | Descripción |
|---|---|---|---|
| id | Integer | PK, indexed | Identificador único de la membresía |
| club_id | Integer | FK → clubs.id | Club al que pertenece |
| user_id | Integer | FK → users.id | Usuario miembro |
| role | String | | Rol del usuario en el club (ej: admin, member) |

### Relationships

| Relación | Tipo | Descripción |
|---|---|---|
| `club` | many-to-one → `clubs` | Club de esta membresía |
| `user` | many-to-one → `users` | Usuario de esta membresía |

---

## club_invitations

Invitaciones para que un usuario se una a un club.

| Columna | Tipo | Constraints | Descripción |
|---|---|---|---|
| id | Integer | PK, indexed | Identificador único de la invitación |
| club_id | Integer | FK → clubs.id | Club que emite la invitación |
| invited_user_id | Integer | FK → users.id | Usuario invitado |
| inviter_id | Integer | FK → users.id | Usuario que realizó la invitación |
| status | String | DEFAULT 'pending' | Estado: `pending`, `accepted`, `rejected`, `cancelled`, `expired` |
| creation_date | DateTime | DEFAULT now() | Fecha de creación de la invitación |
| expiration_date | DateTime | | Fecha de expiración de la invitación |

### Relationships

| Relación | Tipo | Descripción |
|---|---|---|
| `club` | many-to-one → `clubs` | Club que invita |
| `invited_user` | many-to-one → `users` | Usuario invitado |
| `inviter` | many-to-one → `users` | Usuario que invitó |

---

## password_reset_tokens

Tokens para el flujo de recuperación de contraseña.

| Columna | Tipo | Constraints | Descripción |
|---|---|---|---|
| id | Integer | PK, indexed | Identificador único del token |
| user_id | Integer | FK → users.id | Usuario que solicitó el reset |
| token | String | UNIQUE, indexed | Token único enviado por email |
| created_at | DateTime | DEFAULT now() | Fecha de creación |
| expires_at | DateTime | | Fecha de expiración del token |
| used | Boolean | DEFAULT false | Indica si el token ya fue utilizado |

### Relationships

| Relación | Tipo | Descripción |
|---|---|---|
| `user` | many-to-one → `users` | Usuario dueño del token |

---

## matches

Partidos jugados entre dos equipos.

| Columna | Tipo | Constraints | Descripción |
|---|---|---|---|
| id | Integer | PK, indexed | Identificador único del partido |
| club_id | Integer | FK → clubs.id, NULLABLE | Club en el que se jugó el partido |
| created_by | Integer | FK → users.id, NOT NULL | Usuario que creó el registro |
| played_at | DateTime | NOT NULL | Fecha y hora en que se jugó |
| team_a_score | Integer | NOT NULL | Goles del equipo A |
| team_b_score | Integer | NOT NULL | Goles del equipo B |
| created_at | DateTime | DEFAULT now() | Fecha de creación del registro |

### Relationships

| Relación | Tipo | Descripción |
|---|---|---|
| `club` | many-to-one → `clubs` | Club donde se jugó |
| `creator` | many-to-one → `users` | Usuario que registró el partido |
| `match_players` | one-to-many → `match_players` | Jugadores que participaron en el partido |

---

## match_players

Asociación de jugadores a partidos y equipos, con resultado individual.

| Columna | Tipo | Constraints | Descripción |
|---|---|---|---|
| id | Integer | PK, indexed | Identificador único |
| match_id | Integer | FK → matches.id, NOT NULL | Partido al que pertenece |
| player_v1_id | Integer | FK → players.id, NULLABLE | Jugador (tabla players) que participó |
| player_v2_id | Integer | FK → players_v2.id, NULLABLE | Jugador (tabla players_v2) que participó |
| team | String | NOT NULL | Equipo al que pertenece: `A` o `B` |
| result | String | NOT NULL | Resultado individual del jugador: `win`, `loss`, `draw` |

### Constraints

- `ck_match_players_one_player`: Exige que exactamente uno de `player_v1_id` o `player_v2_id` sea NOT NULL.

### Relationships

| Relación | Tipo | Descripción |
|---|---|---|
| `match` | many-to-one → `matches` | Partido |
| `player_v1` | many-to-one → `players` | Jugador (v1) |
| `player_v2` | many-to-one → `players_v2` | Jugador (v2) |

---

## Entity Relationships

```
players.user_id              → users.id
players.club_id              → clubs.id
players.last_modified_by     → users.id

players_v2.user_id           → users.id
players_v2.club_id           → clubs.id
players_v2.last_modified_by  → users.id

skill_votes.player_id        → players.id
skill_votes.voter_id         → users.id

skill_votes_v2.player_id     → players_v2.id
skill_votes_v2.voter_id      → users.id

club_users.club_id           → clubs.id
club_users.user_id           → users.id

club_invitations.club_id          → clubs.id
club_invitations.invited_user_id  → users.id
club_invitations.inviter_id       → users.id

password_reset_tokens.user_id → users.id

matches.club_id             → clubs.id
matches.created_by          → users.id

match_players.match_id      → matches.id
match_players.player_v1_id  → players.id
match_players.player_v2_id  → players_v2.id
```

---

## Notas

- **players vs players_v2 / skill_votes vs skill_votes_v2:** Existen dos versiones paralelas de jugadores y sus votos, ambas activas. La diferencia es la escala de puntuación de habilidades: `players` usa escala **1–5** y `players_v2` usa escala **1–10**. El usuario puede crear jugadores en cualquiera de las dos tablas.
- **email_confirmed:** Usa enteros en lugar de un enum/boolean: `0` (nuevo), `-1` (legacy), `1` (confirmado). Los usuarios legacy pueden hacer login sin confirmar email.
- **photo_data:** Las fotos de jugadores se almacenan como Base64 en Text directamente en la base de datos, no en storage externo.