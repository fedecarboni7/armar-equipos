import asyncio
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.config.llm import get_llm


# Define el template del prompt
formation_prompt = PromptTemplate(
    input_variables=["num_players", "team_data", "allowed_formations"],
    template="""
    Eres un entrenador experto especializado en equipos de fútbol de {num_players} jugadores.
    Basándote en la habilidades de los jugadores listadas a continuación y en las formaciones permitidas con sus posiciones correspondientes, 
    asigna una formación táctica óptima y posiciones a los jugadores.

    Formaciones permitidas:
    {allowed_formations}
    
    Habilidades de los jugadores:
    {team_data}

    Asigna una formación que maximice las fortalezas del equipo, en el siguiente formato JSON:
    {{
      "formation": "X-X-X",
      "players": [
        {{"position": "XX", "name": "Nombre del Jugador"}},
        ...
      ]
    }}

    Donde:
    - "formation" es la formación asignada.
    - "players" es una lista de jugadores con su número de camiseta y posición asignada.
    - "position" es la abreviatura de la posición asignada al jugador.
    - "name" es el nombre del jugador

    Asegúrate de que la formación y las posiciones asignadas sean consistentes con las habilidades de los jugadores.
    """
)

# Crea la cadena LLM
def _get_chain():
    """Create the LLM chain with lazy initialization."""
    return formation_prompt | get_llm() | JsonOutputParser()

chain = _get_chain()

allowed_formations = {
    5: {
        '2-1-1': ['GK', 'CB', 'CB', 'CM', 'ST'],
        '3-0-1': ['GK', 'CB', 'CB', 'CB', 'ST'],
        '2-0-2': ['GK', 'CB', 'CB', 'ST', 'ST'],
        '1-2-1': ['GK', 'CB', 'CM', 'CM', 'ST'],
        '1-1-2': ['GK', 'CB', 'CM', 'ST', 'ST'],
        '1-0-3': ['GK', 'CB', 'ST', 'ST', 'ST']
    },
    9: {
        '3-3-2': ['GK', 'CB', 'CB', 'CB', 'CM', 'CM', 'CM', 'ST', 'ST'],
        '4-2-2': ['GK', 'LB', 'CB', 'CB', 'RB', 'CM', 'CM', 'ST', 'ST'],
        '3-4-1': ['GK', 'CB', 'CB', 'CB', 'LM', 'CM', 'CM', 'RM', 'ST'],
        '4-3-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CM', 'CM', 'CM', 'ST'],
        '3-2-3': ['GK', 'CB', 'CB', 'CB', 'CM', 'CM', 'LW', 'ST', 'RW'],
        '4-1-3': ['GK', 'LB', 'CB', 'CB', 'RB', 'CM', 'LW', 'ST', 'RW']
    },
    11: 
    {
        '4-4-2': ['GK', 'LB', 'CB', 'CB', 'RB', 'LM', 'CM', 'CM', 'RM', 'ST', 'ST'],
        '4-3-3': ['GK', 'LB', 'CB', 'CB', 'RB', 'CM', 'CM', 'CM', 'LW', 'ST', 'RW'],
        '3-4-3': ['GK', 'CB', 'CB', 'CB', 'LM', 'CM', 'CM', 'RM', 'LW', 'ST', 'RW'],
        '4-2-3-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CDM', 'LW', 'CAM', 'RW', 'ST'],
        '5-4-1': ['GK', 'LB', 'CB', 'CB', 'CB', 'RB', 'LM', 'CM', 'CM', 'RM', 'ST'],
        '4-5-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'LM', 'CM', 'CM', 'CM', 'RM', 'ST'],
        '3-5-2': ['GK', 'CB', 'CB', 'CB', 'LM', 'CM', 'CM', 'CM', 'RM', 'ST', 'ST'],
        '5-3-2': ['GK', 'LB', 'CB', 'CB', 'CB', 'RB', 'LM', 'CM', 'RM', 'ST', 'ST'],
        '4-1-4-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'LM', 'CM', 'CM', 'RM', 'ST'],
        '3-4-2-1': ['GK', 'CB', 'CB', 'CB', 'LM', 'CM', 'CM', 'RM', 'AM', 'AM', 'ST']
    }
}

def transformar_datos_jugadores(datos_originales):
    """
    Transforma el diccionario original en una lista de diccionarios con nombres más descriptivos.
    
    Args:
        datos_originales (dict): Diccionario con la estructura original
        
    Returns:
        list: Lista de diccionarios con la estructura mejorada y nombres más descriptivos
    """
    # Mapeo de nombres originales a nombres más descriptivos
    mapeo_atributos = {
        "velocidad": "sprint_speed",
        "resistencia": "stamina",
        "control": "ball_control",
        "pases": "passing",
        "fuerza_cuerpo": "aggressiveness",
        "habilidad_arquero": "goalkeeping",
        "defensa": "defensive_skills",
        "tiro": "finishing",
        "vision": "field_vision"
    }
    
    jugadores_transformados = []
    
    for nombre, datos in datos_originales.items():
        # Creamos un nuevo diccionario para las stats con los nombres actualizados
        stats_nuevas = {}
        for attr_original, valor in datos.items():
            if attr_original in mapeo_atributos:
                stats_nuevas[mapeo_atributos[attr_original]] = valor
        
        jugador = {
            "player_name": nombre,
            "player_id": datos["id"],
            "attributes": stats_nuevas
        }
        jugadores_transformados.append(jugador)
    
    return jugadores_transformados

async def create_formations(players, teams, allowed_formations=allowed_formations):
    """
    Calcula la formación óptima y asigna posiciones a los jugadores.

    Args:
        players (dict): Un diccionario con los datos de los jugadores.
        teams (list): Una lista de listas con los nombres de los jugadores en cada equipo.
        allowed_formations (Dict[int, List[str]]): Un diccionario con las formaciones permitidas por número de jugadores.

    Returns:
        formations (Dict): Un diccionario con las formaciones sugeridas para cada equipo.
    """
    
    formations = {'team1': {}, 'team2': {}}

    # Función auxiliar para invocar chain.ainvoke asíncronamente
    async def get_formation_for_team(team):
        players_by_team = {k: players[k] for k in team[0]}
        players_by_team = transformar_datos_jugadores(players_by_team)
        num_players = len(players_by_team)
        return await chain.ainvoke({"team_data": players_by_team,
                                   "num_players": num_players,
                                   "allowed_formations": allowed_formations[num_players]})

    # Ejecutar todas las invocaciones de forma simultánea
    tasks = [get_formation_for_team(team) for team in teams]
    results = await asyncio.gather(*tasks)

    # Asignar los resultados a sus respectivos equipos
    for i, formation in enumerate(results):
        formations[f'team{i+1}'] = formation

    return formations
