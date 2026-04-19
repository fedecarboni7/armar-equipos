import re
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.config.llm import get_llm

# Limits for input validation
MAX_NAMES = 22 # Maximum player names to match (typical futbol 5/7/11 teams)
MAX_LINES = 30 # Allow extra lines for metadata like match date that user may paste
MAX_NAME_LENGTH = 100
MAX_SKIPPED_NAME_DISPLAY = 50  # Max chars to show for filtered names in error display

# Define el template del prompt para matching de jugadores
player_matching_prompt = PromptTemplate(
    input_variables=["input_names", "available_players"],
    template="""
    Eres un asistente experto en matching de nombres de jugadores de fútbol.
    
    Tu tarea es encontrar coincidencias entre una lista de nombres ingresados por el usuario 
    y una lista de jugadores disponibles en el sistema.
    
    Debes considerar:
    - Nombres abreviados o apodos (ej: "Nahue" debería matchear con "Nahuel")
    - Variaciones de nombres (ej: "Nico" debería matchear con "Nicolás")
    - Errores tipográficos menores (ej: "Jhon" debería matchear con "John")
    - Nombres parciales (ej: "Martinez" podría matchear con "Juan Martinez")
    
    Lista de nombres ingresados por el usuario:
    {input_names}
    
    Lista de jugadores disponibles en el sistema (con sus IDs):
    {available_players}
    
    Responde en el siguiente formato JSON:
    {{
      "matches": [
        {{"input_name": "nombre ingresado", "matched_player_id": id_del_jugador, "matched_player_name": "nombre del jugador", "confidence": "high/medium/low"}},
        ...
      ],
      "not_found": ["nombre1", "nombre2", ...]
    }}
    
    Reglas:
    - Solo incluye matches cuando tengas suficiente confianza de que son la misma persona
    - Si un nombre ingresado podría matchear con múltiples jugadores, elige el más probable
    - Si no encuentras match para un nombre, inclúyelo en "not_found"
    - La confianza debe ser "high" si es una coincidencia clara, "medium" si hay algo de ambigüedad, 
      "low" si es una coincidencia posible pero no segura
    """
)


def _get_chain():
    """Create the LLM chain with lazy initialization."""
    return player_matching_prompt | get_llm() | JsonOutputParser()


def sanitize_name(name: str) -> str:
    """Sanitize a player name to prevent prompt injection."""
    # Remove control characters and limit length
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)
    # Remove potential prompt injection patterns
    sanitized = re.sub(r'[{}\[\]<>]', '', sanitized)
    return sanitized[:MAX_NAME_LENGTH].strip()


def validate_and_sanitize_names(input_names: list[str]) -> tuple[list[str], list[str]]:
    """
    Validate and sanitize input names.
    
    Returns:
        Tuple of (valid_names, skipped_names)
    """
    valid_names = []
    skipped_names = []
    
    for name in input_names[:MAX_LINES]:  # Limit total lines processed
        if len(valid_names) >= MAX_NAMES:
            if name.strip():  # Additional names beyond MAX_NAMES are treated as skipped
                skipped_names.append(name.strip()[:MAX_SKIPPED_NAME_DISPLAY])
            continue
        
        sanitized = sanitize_name(name)
        if sanitized and len(sanitized) >= 2:  # Minimum 2 characters for a valid name
            valid_names.append(sanitized)
        elif name.strip():  # Original had content but was filtered out
            skipped_names.append(name.strip()[:MAX_SKIPPED_NAME_DISPLAY])
    
    return valid_names, skipped_names


def validate_ai_response(result: dict, available_players: list[dict]) -> dict:
    """
    Validate and sanitize the AI response to ensure correct structure and valid player IDs.
    
    Args:
        result: Raw response from AI
        available_players: List of valid players
        
    Returns:
        Validated and sanitized response dict
    """
    # Build set of valid player IDs
    valid_player_ids = {p["id"] for p in available_players}
    
    # Extract matches and not_found with type checking
    matches = result.get("matches", [])
    not_found = result.get("not_found", [])
    
    if not isinstance(matches, list):
        matches = []
    if not isinstance(not_found, list):
        not_found = [str(not_found)] if not_found else []
    
    validated_matches = []
    for match in matches:
        if not isinstance(match, dict):
            continue
        
        matched_player_id = match.get("matched_player_id")
        input_name = match.get("input_name")
        matched_player_name = match.get("matched_player_name")
        confidence = match.get("confidence", "low")
        
        # Validate player ID exists
        if matched_player_id is None or matched_player_id not in valid_player_ids:
            if input_name and input_name not in not_found:
                not_found.append(str(input_name))
            continue
        
        # Validate confidence value
        if confidence not in ("high", "medium", "low"):
            confidence = "low"
        
        validated_matches.append({
            "input_name": str(input_name) if input_name else "",
            "matched_player_id": matched_player_id,
            "matched_player_name": str(matched_player_name) if matched_player_name else "",
            "confidence": confidence
        })
    
    return {
        "matches": validated_matches,
        "not_found": [str(n) for n in not_found if n]
    }


async def match_players(input_names: list[str], available_players: list[dict]) -> dict:
    """
    Usa IA para encontrar coincidencias entre nombres ingresados y jugadores disponibles.
    
    Args:
        input_names: Lista de nombres ingresados por el usuario
        available_players: Lista de diccionarios con {id, name} de jugadores disponibles
        
    Returns:
        Dict con matches encontrados y nombres no encontrados
        
    Raises:
        ValueError: If input validation fails
    """
    # Validate and sanitize input names
    valid_names, skipped_names = validate_and_sanitize_names(input_names)
    
    if not valid_names:
        return {"matches": [], "not_found": skipped_names or input_names}
    
    # Formatear la lista de jugadores disponibles para el prompt
    players_formatted = "\n".join([f"- ID: {p['id']}, Nombre: {p['name']}" for p in available_players])
    names_formatted = "\n".join([f"- {name}" for name in valid_names])
    
    # Get chain with lazy initialization
    chain = _get_chain()
    
    result = await chain.ainvoke({
        "input_names": names_formatted,
        "available_players": players_formatted
    })
    
    # Validate AI response
    validated_result = validate_ai_response(result, available_players)
    
    # Add any skipped names to not_found
    if skipped_names:
        validated_result["not_found"].extend(skipped_names)
    
    return validated_result
