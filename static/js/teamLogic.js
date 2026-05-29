
function getTeamSkills(players) {
    var skills = {
        velocidad: 0,
        resistencia: 0,
        control: 0,
        pases: 0,
        tiro: 0,
        defensa: 0,
        habilidad_arquero: 0,
        fuerza_cuerpo: 0,
        vision: 0,
        total: 0
    };

    // Obtener las habilidades de los jugadores leyendo playerDataDict
    players.forEach(function(player) {
        var playerSkills = playerDataDict[player];
        for (var skill in playerSkills) {
            if (skill === "id") {
                continue;
            }
            skills[skill] += playerSkills[skill];
        }
    });

    // Calcular el total de habilidades
    skills.total = Object.values(skills).reduce(function(total, value) {
        return total + value;
    }, 0);

    return skills;
}

function swapPlayer(player, fromTeamIndex, toTeamIndex) {
    // Obtener las listas de jugadores de ambos equipos
    var fromTeamList = document.querySelector(`.team-list[data-index='${fromTeamIndex}']`);
    var toTeamList = document.querySelector(`.team-list[data-index='${toTeamIndex}']`);

    // Buscar el elemento del jugador en la lista del equipo de origen
    var playerElement = Array.from(fromTeamList.children).find(function(element) {
        return element.querySelector(".player-name").textContent === player;
    });

    // Remover el jugador del equipo de origen
    if (playerElement) {
        fromTeamList.removeChild(playerElement);
        
        // Crear un nuevo elemento de lista para el jugador en el equipo de destino
        var newPlayerElement = document.createElement("li");
        newPlayerElement.classList.add("player-item");
        
        // Crear el span para el número del jugador
        var playerNumberSpan = document.createElement("span");
        playerNumberSpan.classList.add("player-number");
        // El número será la cantidad de elementos actuales + 1
        playerNumberSpan.textContent = (toTeamList.children.length + 1) + ".";

        // Crear el span para el nombre del jugador
        var playerNameSpan = document.createElement("span");
        playerNameSpan.classList.add("player-name");
        playerNameSpan.textContent = player;

        // Crear el botón de swap
        var swapButton = document.createElement("button");
        swapButton.type = "button";
        swapButton.classList.add("swap-button");
        swapButton.innerHTML = `<i class="fa-solid fa-right-left"></i>`;
        swapButton.onclick = function() {
            swapPlayer(player, toTeamIndex, fromTeamIndex);
        };

        // Añadir todos los elementos en orden
        newPlayerElement.appendChild(playerNumberSpan);
        newPlayerElement.appendChild(playerNameSpan);
        newPlayerElement.appendChild(swapButton);

        // Añadir el nuevo elemento de lista al equipo de destino
        toTeamList.appendChild(newPlayerElement);
        
        // Actualizar los números de todos los jugadores en ambos equipos
        renumerarJugadoresEquipo(fromTeamList);
        renumerarJugadoresEquipo(toTeamList);
    }

    // Definir equipo 1 y equipo 2
    var team1Index = fromTeamIndex;
    var team2Index = toTeamIndex;
    if (fromTeamIndex > toTeamIndex) {
        team1Index = toTeamIndex;
        team2Index = fromTeamIndex;
    }

    // Actualizar la tabla de habilidades
    updateSkillsTable(team1Index, team2Index);

    // Actualizar el gráfico de radar
    var containerNumber = Math.floor(team1Index / 2) + 1;
    var contentContainer = document.getElementById('content-container' + containerNumber);
    createRadarChart(contentContainer);
}

function updateSkillsTable(team1Index, team2Index) {
    let team1List = document.querySelector(`.team-list[data-index='${team1Index}']`);
    let team2List = document.querySelector(`.team-list[data-index='${team2Index}']`);

    // Obtener los nombres de los jugadores de ambos equipos
    var team1Players = Array.from(team1List.children).map(function(element) {
        return element.querySelector(".player-name").textContent;
    });
    var team2Players = Array.from(team2List.children).map(function(element) {
        return element.querySelector(".player-name").textContent;
    });

    // Obtener las habilidades de los jugadores de ambos equipos
    var team1Skills = getTeamSkills(team1Players);
    var team2Skills = getTeamSkills(team2Players);

    // Actualizar la tabla específica de habilidades que representa la comparación de ambos equipos
    var tableNumber = Math.floor(team1Index / 2) + 1;
    var table = document.getElementById("skills-table" + tableNumber);
    var rows = table.querySelectorAll("tbody tr");
    var skills = ["velocidad", "resistencia", "control", "pases", "tiro", "defensa", "habilidad_arquero", "fuerza_cuerpo", "vision", "total"];
    for (var i = 0; i < skills.length; i++) {
        var row = rows[i];
        var cells = row.querySelectorAll("td");
        cells[1].textContent = team1Skills[skills[i]];
        cells[2].textContent = team2Skills[skills[i]];
    }
}

// Validación de equipos para formaciones (sin el fetch)
function validateAndPrepareTeamsForFormations(indice) {
    // Obtener los índices de los equipos
    const team1 = indice * 2 - 2;
    const team2 = indice * 2 - 1;
    // Hacer una lista de las listas de equipos
    const teamsList = [teams[team1], teams[team2]];

    // Validar que la cantidad de jugadores por equipo sea de 5, 9 o 11 (para futsal, fútbol 9 o fútbol 11)
    if (teamsList[0][0].length !== 11 && teamsList[0][0].length !== 9 && teamsList[0][0].length !== 5) {
        alert('La cantidad de jugadores por equipo debe ser de 5, 9 u 11.');
        return null;
    }
    if (teamsList[1][0].length !== 11 && teamsList[1][0].length !== 9 && teamsList[1][0].length !== 5) {
        alert('La cantidad de jugadores por equipo debe ser de 5, 9 u 11.');
        return null;
    }

    // Preparar los datos a enviar al backend
    const payload = {
        player_data_dict: playerDataDict,  // Enviar el objeto directamente
        teams: teamsList
    };

    return payload;
}
