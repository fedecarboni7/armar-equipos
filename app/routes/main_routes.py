import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from requests import Session

from app.config.config import templates
from app.db.database import get_db
from app.db.database_utils import execute_with_retries, query_clubs, query_players
from app.db.models import User
from app.utils.ai_formations import create_formations
from app.utils.ai_player_matcher import match_players, MAX_LINES
from app.utils.auth import get_current_user
from app.utils.team_optimizer import find_best_combination

router = APIRouter()

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing_page(request: Request):
    return templates.TemplateResponse(request=request, name="landing-page.html")


@router.get("/jugadores", response_class=HTMLResponse, include_in_schema=False)
async def players_page(
        request: Request,
        current_user: User = Depends(get_current_user)
    ):
    if not current_user:
        return RedirectResponse("/login", status_code=302)
    
    return templates.TemplateResponse(request=request, name="players.html", context={
        "request": request,
        "user": current_user
    })


@router.get("/clubes", response_class=HTMLResponse, include_in_schema=False)
async def clubs_management_page(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    if not current_user:
        return RedirectResponse("/login", status_code=302)
    
    # Obtener clubes del usuario
    clubs = execute_with_retries(query_clubs, db, current_user.id)
    
    # Preparar datos del usuario actual para el template
    current_user_data = {
        "id": current_user.id,
        "username": current_user.username,
        "clubRole": None  # Se actualizará dinámicamente según el club seleccionado
    }
    
    return templates.TemplateResponse(request=request, name="clubs.html", context={
        "request": request,
        "user": current_user,
        "userClubs": clubs,
        "currentUser": current_user_data
    })


@router.get("/home", response_class=HTMLResponse, include_in_schema=False)
async def armar_equipos_page(
        request: Request,
        current_user: User = Depends(get_current_user)
    ):
    if not current_user:
        return RedirectResponse("/", status_code=302)
    
    return templates.TemplateResponse(request=request, name="armar_equipos.html", context={
        "request": request,
        "user": current_user
    })

@router.post("/formations", include_in_schema=False, response_class=JSONResponse)
async def show_formations(
        request: Request,
        current_user: User = Depends(get_current_user)
    ):
    if not current_user:
        request.session.clear()
        return RedirectResponse("/", status_code=302)
    
    # Recibir los datos del frontend
    data = await request.json()
    
    # Extraer los valores del diccionario JSON recibido
    player_data_dict = data.get('player_data_dict')
    teams = data.get('teams')
    
    # Generar las formaciones
    formations = await create_formations(player_data_dict, teams)

    # Retornar las formaciones como respuesta JSON
    return JSONResponse(content=formations)

@router.post("/api/build-teams", response_class=JSONResponse)
async def build_teams_api(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    if not current_user:
        return JSONResponse(content={"error": "No autenticado"}, status_code=401)
    
    try:
        data = await request.json()
        selected_player_ids = data.get('selected_player_ids', [])
        
        if len(selected_player_ids) < 4:
            return JSONResponse(content={"error": "Necesitas al menos 4 jugadores para armar equipos"}, status_code=400)
        
        # Obtener datos de los jugadores seleccionados
        current_user_id = current_user.id
        club_id = data.get('club_id')
        scale = data.get('scale', '1-5')
        
        if club_id:
            all_players = execute_with_retries(query_players, db, current_user_id, club_id, scale)
        else:
            all_players = execute_with_retries(query_players, db, current_user_id, scale=scale)
        
        # Filtrar solo jugadores seleccionados
        selected_players = [p for p in all_players if p.id in selected_player_ids]
        
        if len(selected_players) != len(selected_player_ids):
            return JSONResponse(content={"error": "Algunos jugadores no fueron encontrados"}, status_code=400)
        
        # Preparar datos para el algoritmo
        player_scores = [
            [
                p.velocidad,
                p.resistencia,
                p.control,
                p.pases,
                p.tiro,
                p.defensa,
                p.habilidad_arquero,
                p.fuerza_cuerpo,
                p.vision,
            ]
            for p in selected_players
        ]
        
        # Generar equipos
        mejores_equipos, min_difference_total = find_best_combination(player_scores)
        
        # Formatear respuesta
        teams_options = []
        for equipos in mejores_equipos:
            team1_players = [selected_players[i] for i in equipos[0]]
            team2_players = [selected_players[i] for i in equipos[1]]
            
            teams_options.append({
                "team1": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "velocidad": p.velocidad,
                        "resistencia": p.resistencia,
                        "control": p.control,
                        "pases": p.pases,
                        "tiro": p.tiro,
                        "defensa": p.defensa,
                        "habilidad_arquero": p.habilidad_arquero,
                        "fuerza_cuerpo": p.fuerza_cuerpo,
                        "vision": p.vision
                    }
                    for p in team1_players
                ],
                "team2": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "velocidad": p.velocidad,
                        "resistencia": p.resistencia,
                        "control": p.control,
                        "pases": p.pases,
                        "tiro": p.tiro,
                        "defensa": p.defensa,
                        "habilidad_arquero": p.habilidad_arquero,
                        "fuerza_cuerpo": p.fuerza_cuerpo,
                        "vision": p.vision
                    }
                    for p in team2_players
                ]
            })
        
        return JSONResponse(content={
            "teams": teams_options,
            "difference": min_difference_total
        })
        
    except Exception as e:
        logging.exception("Error building teams: %s", str(e))
        return JSONResponse(content={"error": "Error interno al armar equipos"}, status_code=500)


@router.post("/api/match-players", response_class=JSONResponse)
async def match_players_api(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    """
    Endpoint para buscar coincidencias entre nombres de jugadores ingresados
    y jugadores disponibles en el sistema usando IA.
    """
    if not current_user:
        return JSONResponse(content={"error": "No autenticado"}, status_code=401)
    
    try:
        data = await request.json()
        input_names = data.get('input_names', [])
        club_id = data.get('club_id')
        scale = data.get('scale', '1-5')
        
        # Validate input_names is a list
        if not isinstance(input_names, list):
            return JSONResponse(content={"error": "input_names debe ser una lista"}, status_code=400)
        
        if not input_names:
            return JSONResponse(content={"error": "No se proporcionaron nombres"}, status_code=400)
        
        # Limit is enforced in match_players, but provide early feedback
        if len(input_names) > MAX_LINES:
            return JSONResponse(
                content={"error": f"Se permiten máximo {MAX_LINES} líneas. Por favor, reduce la lista."},
                status_code=400
            )
        
        # Obtener jugadores disponibles según el contexto
        current_user_id = current_user.id
        
        # Autorizar acceso al club solicitado (si se especifica)
        if club_id is not None:
            user_clubs = execute_with_retries(query_clubs, db, current_user_id)
            user_club_ids = {club.id for club in user_clubs} if user_clubs else set()
            if club_id not in user_club_ids:
                return JSONResponse(
                    content={"error": "No tienes permisos para acceder a este club"},
                    status_code=403
                )
        
        all_players = execute_with_retries(query_players, db, current_user_id, club_id, scale)
        
        if not all_players:
            return JSONResponse(content={"error": "No hay jugadores disponibles"}, status_code=400)
        
        # Formatear jugadores para el matcher
        available_players = [{"id": p.id, "name": p.name} for p in all_players]
        
        # Usar IA para hacer el matching
        result = await match_players(input_names, available_players)
        
        return JSONResponse(content=result)
    
    except ValueError as e:
        logging.warning("Validation error in match_players: %s", str(e))
        return JSONResponse(
            content={"error": "Error de validación en los datos enviados"},
            status_code=400
        )
    except Exception as e:
        logging.exception("Error matching players: %s", str(e))
        return JSONResponse(content={"error": "Error al buscar coincidencias de jugadores"}, status_code=500)