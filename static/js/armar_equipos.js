// Variables globales
let players = [];
let selectedPlayers = new Set();
let teamA = [];
let teamB = [];
let availablePlayers = [];
let filteredPlayers = [];
// Variables para el contexto actual (ahora se manejan desde clubSelector.js)
// let currentClubId = 'my-players';  // Comentado - se usa desde clubSelector.js  
// let userClubs = [];               // Comentado - se usa desde clubSelector.js
let currentScale = 5; // Variable para la escala actual
let loading = false;
let hasResults = false; // Variable para saber si hay resultados generados

// Import limits - should match backend MAX_LINES in ai_player_matcher.py
const MAX_IMPORT_LINES = 30;

// ==================== HELP MODAL ====================
const HELP_MODAL_KEY = 'armarEquipos_helpModalShown';

function initHelpModal() {
    const modal = document.getElementById('help-modal');
    const helpBtn = document.getElementById('help-btn');
    const closeBtn = document.getElementById('close-help-modal');
    const startBtn = document.getElementById('start-btn');
    
    if (!modal) return;
    
    // Mostrar modal si es la primera vez
    const hasSeenHelp = localStorage.getItem(HELP_MODAL_KEY);
    if (!hasSeenHelp) {
        showHelpModal();
    }
    
    // Event listeners
    helpBtn?.addEventListener('click', showHelpModal);
    closeBtn?.addEventListener('click', closeHelpModal);
    startBtn?.addEventListener('click', closeHelpModal);
    
    // Cerrar al hacer click fuera del modal
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeHelpModal();
        }
    });
    
    // Cerrar con Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeHelpModal();
        }
    });
    
    function showHelpModal() {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    function closeHelpModal() {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        
        // Guardar en localStorage que ya vio el modal
        localStorage.setItem(HELP_MODAL_KEY, 'true');
    }
}
// ==================== END HELP MODAL ====================

// Initialize app
async function init() {
    try {
        // Inicializar modal de ayuda
        initHelpModal();
        
        // Inicializar modal de importar lista
        initImportModal();
        
        // El clubSelector.js se encarga de cargar los clubes automáticamente
        
        // Cargar jugadores
        await loadPlayers();
        
        // Configurar event listeners
        setupEventListeners();
        
        // Renderizar interfaz
        renderPlayers();
        updateManualMode();
    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Error al cargar la aplicación');
    }
}

// Función de integración con clubSelector.js
// Esta función se llama cuando cambia el contexto desde el selector común
function onContextChanged(contextId) {
    return loadPlayersForContext(contextId);
}

// Cargar jugadores (usando la misma lógica que players.js)
async function loadPlayers() {
    await loadPlayersForContext(getCurrentClubId());
}

// Cargar jugadores según el contexto (personal o club) - igual que en players.js
async function loadPlayersForContext(contextId) {
    try {
        loading = true;
        renderPlayers(); // Mostrar loading
        
        const scale = currentScale === 5 ? '1-5' : '1-10';
        let url = `/api/players?scale=${scale}`;
        
        if (contextId !== 'my-players') {
            url += `&club_id=${contextId}`;
        }
        
        const response = await fetch(url, {
            method: 'GET',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) throw new Error(`Error ${response.status}`);
        const data = await response.json();
        players = data.players || data; // Manejar tanto {players: [...]} como [...]
        
        // Calcular promedio para cada jugador
        players = players.map(player => ({
            ...player,
            rating: calculateAverage(player)
        }));
        
        // Inicializar jugadores filtrados con todos los jugadores
        filteredPlayers = [...players];
        availablePlayers = [...players];
        
        // Limpiar selecciones cuando cambia el contexto
        selectedPlayers.clear();
        teamA = [];
        teamB = [];
        hasResults = false; // Resetear resultados cuando cambia el contexto
        
        // Ocultar resultados anteriores si existen
        const resultsContainer = document.getElementById('teams-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }
        
        // Limpiar el buscador cuando cambia el contexto
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.value = '';
        }
        
        loading = false;
        renderPlayers();
        updateManualMode();
        
    } catch (error) {
        loading = false;
        console.error('Error loading players for context:', error);
        showError('Error al cargar jugadores');
        players = [];
        filteredPlayers = [];
        availablePlayers = [];
        renderPlayers();
    }
}

// Función para cambiar escala (igual que en players.js)
function setScale(scale) {
    currentScale = scale;
    
    // Actualizar botones activos
    document.querySelectorAll('.scale-option').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Recargar jugadores de la tabla correspondiente
    loadPlayers();
}

// Calcular promedio de habilidades
function calculateAverage(player) {
    const skillKeys = ['velocidad', 'resistencia', 'pases', 'tiro', 'defensa', 'fuerza_cuerpo', 'control', 'habilidad_arquero', 'vision'];
    const skillValues = skillKeys.map(key => player[key]).filter(val => typeof val === 'number');
    
    if (skillValues.length === 0) return 0;
    
    const average = skillValues.reduce((a, b) => a + b, 0) / skillValues.length;
    return Math.round(average * 10) / 10;
}

function setupEventListeners() {
    // Mode selector
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            const mode = e.target.dataset.mode;
            document.getElementById('automatic-mode').classList.toggle('hidden', mode !== 'automatic');
            document.getElementById('manual-mode').classList.toggle('hidden', mode !== 'manual');
            
            // Manejar visibilidad de resultados generados
            const resultsContainer = document.getElementById('teams-results');
            if (resultsContainer) {
                if (mode === 'manual') {
                    // Ocultar resultados cuando se pasa a modo manual
                    resultsContainer.style.display = 'none';
                } else if (mode === 'automatic' && hasResults) {
                    // Mostrar resultados cuando se vuelve a modo automático y hay resultados
                    resultsContainer.style.display = 'block';
                }
            }
        });
    });

    // Search functionality
    document.getElementById('search-input').addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        filteredPlayers = players.filter(player => 
            player.name.toLowerCase().includes(searchTerm)
        );
        renderPlayers();
    });

    // Generate teams button
    document.querySelector('.generate-btn').addEventListener('click', generateTeams);
}

function renderPlayers() {
    const playersList = document.getElementById('players-list');
    
    if (loading) {
        playersList.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div style="font-size: 18px; color: #aaa; margin-bottom: 10px;">⚽ Cargando jugadores...</div>
                <div style="font-size: 14px; color: #666;">Esto puede tomar unos segundos</div>
            </div>
        `;
        return;
    }
    
    playersList.innerHTML = '';

    const playersToShow = filteredPlayers;
    
    if (playersToShow.length === 0) {
        const contextName = getCurrentClubId() === 'my-players' ? 'creados' : 
                          getUserClubs().find(club => club.id == getCurrentClubId())?.name || 'de este club';
        
        const searchTerm = document.getElementById('search-input')?.value?.toLowerCase().trim() || '';
        
        // Mostrar mensaje diferente si es por búsqueda o por falta de jugadores
        const message = searchTerm !== '' ? 
            `🔍 No se encontraron jugadores con "${escapeHTML(searchTerm)}"` :
            `👤 No hay jugadores ${contextName}`;
        
        const subMessage = searchTerm !== '' ?
            'Intenta con otro término de búsqueda' :
            '¡Agrega jugadores para comenzar a armar equipos!';
        
        const button = searchTerm === '' ?
            '<a href="/jugadores" style="display: inline-block; margin-top: 20px; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 8px; font-weight: 500; transition: background-color 0.3s;">Ir a Jugadores</a>' :
            '';
        
        playersList.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div style="font-size: 18px; color: #aaa; margin-bottom: 10px;">${message}</div>
                <div style="font-size: 14px; color: #666;">${subMessage}</div>
                ${button}
            </div>
        `;
        return;
    }

    filteredPlayers.forEach(player => {
        const playerItem = document.createElement('div');
        playerItem.className = 'player-item';
        
        const isSelected = selectedPlayers.has(player.name);
        
        playerItem.innerHTML = `
            <div class="player-info">
                <div class="checkbox ${isSelected ? 'checked' : ''}" data-player="${player.name}"></div>
                <span class="player-name">${player.name}</span>
            </div>
            <span class="player-rating">${player.rating}/${currentScale}</span>
        `;
        
        // Add click event to entire player item
        playerItem.addEventListener('click', () => {
            togglePlayerSelection(player.name);
        });
        
        // Add cursor pointer style
        playerItem.style.cursor = 'pointer';
        
        playersList.appendChild(playerItem);
    });

    updatePlayersCount();
}

function togglePlayerSelection(playerName) {
    if (selectedPlayers.has(playerName)) {
        selectedPlayers.delete(playerName);
    } else {
        selectedPlayers.add(playerName);
    }
    renderPlayers();
}

function updatePlayersCount() {
    const count = selectedPlayers.size;
    document.getElementById('players-count').textContent = `Seleccionados: ${count} jugadores`;
}

// Manual mode functions
function updateManualMode() {
    renderAvailablePlayers();
    renderTeamPlayers();
    updateTeamCounts();
    renderManualComparison();
}

function renderAvailablePlayers() {
    const container = document.getElementById('available-players-list');
    container.innerHTML = '';

    if (availablePlayers.length === 0 && players.length === 0) {
        const contextName = getCurrentClubId() === 'my-players' ? 'creados' : 
                          getUserClubs().find(club => club.id == getCurrentClubId())?.name || 'de este club';
        container.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div style="font-size: 18px; color: #aaa; margin-bottom: 10px;">👤 No hay jugadores ${contextName}</div>
                <div style="font-size: 14px; color: #666;">¡Agrega jugadores para comenzar a armar equipos!</div>
                <a href="/jugadores" style="display: inline-block; margin-top: 20px; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 8px; font-weight: 500; transition: background-color 0.3s;">Ir a Jugadores</a>
            </div>
        `;
        return;
    }

    availablePlayers.forEach(player => {
        const playerDiv = document.createElement('div');
        playerDiv.className = 'available-player';
        playerDiv.innerHTML = `
            <div class="player-info">
                <span class="player-name">👤 ${player.name}</span>
                <span class="player-rating">${player.rating}</span>
            </div>
            <div class="add-buttons">
                <button class="add-btn" onclick="addToTeam('A', '${player.name}')">1</button>
                <button class="add-btn team-b" onclick="addToTeam('B', '${player.name}')">2</button>
            </div>
        `;
        container.appendChild(playerDiv);
    });
}

function renderTeamPlayers() {
    renderTeam('A', teamA, 'team-a-players');
    renderTeam('B', teamB, 'team-b-players');
}

function renderTeam(teamName, team, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    team.forEach(player => {
        const playerDiv = document.createElement('div');
        playerDiv.className = 'team-player';
        playerDiv.innerHTML = `
            <div class="player-info">
                <span class="player-name">👤 ${player.name}</span>
                <span class="player-rating">${player.rating}</span>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <button class="swap-btn" onclick="swapTeam('${teamName}', '${player.name}')"><i class="fa-solid fa-right-left"></i></button>
                <button class="remove-btn" onclick="removeFromTeam('${teamName}', '${player.name}')"><i class="fa-solid fa-xmark"></i></button>
            </div>
        `;
        container.appendChild(playerDiv);
    });
}

// Renderizar gráficos de comparación en modo manual reutilizando el layout de results
function renderManualComparison() {
    // Crear contenedor si no existe
    let comparison = document.getElementById('manual-comparison');
    if (!comparison) {
        const manualMode = document.getElementById('manual-mode');
        comparison = document.createElement('div');
        comparison.id = 'manual-comparison';
        comparison.className = 'stats-container';
        manualMode.appendChild(comparison);
    }

    // Si no hay jugadores en ambos equipos, ocultar
    const teamSize = Math.min(teamA.length, teamB.length);
    if (teamSize === 0) {
        comparison.style.display = 'none';
        comparison.innerHTML = '';
        return;
    }

    // Construir tabla de habilidades y contenedores de gráficos como en results
    const skills = [
        ['velocidad', 'Velocidad'],
        ['resistencia', 'Resistencia'],
        ['control', 'Control'],
        ['pases', 'Pases'],
        ['fuerza_cuerpo', 'Fuerza cuerpo'],
        ['habilidad_arquero', 'Hab. Arquero'],
        ['defensa', 'Defensa'],
        ['tiro', 'Tiro'],
        ['vision', 'Visión'],
    ];

    // Calcular totales por equipo
    const totalsA = Object.fromEntries(skills.map(([k]) => [k, 0]));
    const totalsB = Object.fromEntries(skills.map(([k]) => [k, 0]));
    teamA.forEach(p => skills.forEach(([k]) => totalsA[k] += p[k] || 0));
    teamB.forEach(p => skills.forEach(([k]) => totalsB[k] += p[k] || 0));
    const totalA = Object.values(totalsA).reduce((a,b)=>a+b,0);
    const totalB = Object.values(totalsB).reduce((a,b)=>a+b,0);

    comparison.style.display = 'block';
    comparison.innerHTML = `
        <div class="button-container">
            <button type="button" id="mostrarDetallesManual" class="details-btn">
                <i class="fas fa-chart-bar" style="padding-right: 5px;"></i>
                <span>Mostrar detalles</span>
            </button>
        </div>
        <div class="content-container" id="content-containerManual" data-players-count="${teamSize}" style="display: none;">
            <div class="carousel-container">
                <div class="carousel-slides">
                    <div class="carousel-slide">
                        <div class="table-container">
                            <table id="skills-tableManual">
                                <thead>
                                    <tr>
                                        <th>Habilidad</th>
                                        <th>Equipo 1</th>
                                        <th>Equipo 2</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${skills.map(([k, label]) => `
                                        <tr>
                                            <td>${label}</td>
                                            <td>${totalsA[k]}</td>
                                            <td>${totalsB[k]}</td>
                                        </tr>
                                    `).join('')}
                                    <tr>
                                        <td>Total</td>
                                        <td>${totalA}</td>
                                        <td>${totalB}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="carousel-slide">
                        <div class="chart-container">
                            <canvas></canvas>
                        </div>
                    </div>
                </div>
                <button class="carousel-btn carousel-prev">❮</button>
                <button class="carousel-btn carousel-next">❯</button>
            </div>
        </div>
    `;

    // Wire up toggle
    const btn = document.getElementById('mostrarDetallesManual');
    btn.onclick = () => {
        const container = document.getElementById('content-containerManual');
        const textSpan = btn.querySelector('span');
        if (container.style.display === 'none' || container.style.display === '') {
            container.style.display = 'flex';
            textSpan.textContent = 'Ocultar detalles';
            // Pasar conteo de jugadores para escalar gráficos
            container.dataset.playersCount = String(teamSize);
            createRadarChart(container);
            createCarousel(container.querySelector('.carousel-container'));
        } else {
            container.style.display = 'none';
            textSpan.textContent = 'Mostrar detalles';
        }
    };
}

function updateTeamCounts() {
    document.getElementById('team-a-count').textContent = `${teamA.length} jugadores`;
    document.getElementById('team-b-count').textContent = `${teamB.length} jugadores`;
    document.getElementById('available-count').textContent = `${availablePlayers.length} jugadores`;
}

function addToTeam(teamName, playerName) {
    const player = availablePlayers.find(p => p.name === playerName);
    if (!player) return;

    if (teamName === 'A') {
        teamA.push(player);
    } else {
        teamB.push(player);
    }

    availablePlayers = availablePlayers.filter(p => p.name !== playerName);
    updateManualMode();
}

function removeFromTeam(teamName, playerName) {
    let player;
    
    if (teamName === 'A') {
        player = teamA.find(p => p.name === playerName);
        teamA = teamA.filter(p => p.name !== playerName);
    } else {
        player = teamB.find(p => p.name === playerName);
        teamB = teamB.filter(p => p.name !== playerName);
    }

    if (player) {
        availablePlayers.push(player);
        availablePlayers.sort((a, b) => a.name.localeCompare(b.name));
    }
    
    updateManualMode();
}

function swapTeam(currentTeam, playerName) {
    let player;
    
    if (currentTeam === 'A') {
        player = teamA.find(p => p.name === playerName);
        teamA = teamA.filter(p => p.name !== playerName);
        teamB.push(player);
    } else {
        player = teamB.find(p => p.name === playerName);
        teamB = teamB.filter(p => p.name !== playerName);
        teamA.push(player);
    }
    
    updateManualMode();
}

// Generate optimized teams function
async function generateTeams() {
    const generateBtn = document.querySelector('.generate-btn');
    
    // Validate that there are selected players
    if (selectedPlayers.size < 3) {
        alert('Necesitas seleccionar al menos 3 jugadores para armar equipos');
        return;
    }
    
    // Get player IDs from selected player names
    const selectedPlayerIds = Array.from(selectedPlayers).map(playerName => {
        const player = players.find(p => p.name === playerName);
        return player ? player.id : null;
    }).filter(id => id !== null);
    
    if (selectedPlayerIds.length !== selectedPlayers.size) {
        alert('Error: No se pudieron encontrar algunos jugadores seleccionados');
        return;
    }
    
    // Show loading state
    const originalText = generateBtn.innerHTML;
    generateBtn.innerHTML = '⚽ Generando equipos...';
    generateBtn.disabled = true;
    
    try {
        // Prepare data for API call
        const requestData = {
            selected_player_ids: selectedPlayerIds,
            club_id: getCurrentClubId() !== 'my-players' ? parseInt(getCurrentClubId()) : null,
            scale: currentScale === 5 ? '1-5' : '1-10'
        };
        
        // Call the backend API
        const response = await fetch('/api/build-teams', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al generar equipos');
        }
        
        const data = await response.json();
        
        // Transform API response to format expected by results template
        const transformedData = transformTeamsData(data);
        
        // Render the results
        displayTeamsResults(transformedData);
        
    } catch (error) {
        console.error('Error generating teams:', error);
        alert('Error al generar equipos: ' + error.message);
    } finally {
        // Restore button state
        generateBtn.innerHTML = originalText;
        generateBtn.disabled = false;
    }
}

// Transform API response to format expected by results template
function transformTeamsData(apiData) {
    const teams = [];
    const skills = {
        "velocidad": "Velocidad", 
        "resistencia": "Resistencia", 
        "control": "Control", 
        "pases": "Pases", 
        "fuerza_cuerpo": "Fuerza cuerpo", 
        "habilidad_arquero": "Hab. Arquero", 
        "defensa": "Defensa", 
        "tiro": "Tiro", 
        "vision": "Visión"
    };
    
    // Create player data dictionary for global access
    window.playerDataDict = {};
    
    apiData.teams.forEach((teamOption, optionIndex) => {
        // Process team 1
        const team1Players = teamOption.team1.map(p => p.name);
        const team1Skills = calculateTeamSkills(teamOption.team1);
        teams.push([team1Players, team1Skills]);
        
        // Process team 2  
        const team2Players = teamOption.team2.map(p => p.name);
        const team2Skills = calculateTeamSkills(teamOption.team2);
        teams.push([team2Players, team2Skills]);
        
        // Add players to global dictionary
        [...teamOption.team1, ...teamOption.team2].forEach(player => {
            window.playerDataDict[player.name] = {
                id: player.id,
                velocidad: player.velocidad,
                resistencia: player.resistencia,
                control: player.control,
                pases: player.pases,
                fuerza_cuerpo: player.fuerza_cuerpo,
                habilidad_arquero: player.habilidad_arquero,
                defensa: player.defensa,
                tiro: player.tiro,
                vision: player.vision
            };
        });
    });
    
    // Store teams in global variable for other functions
    window.teams = teams;
    
    return {
        teams: teams,
        skills: skills,
        min_difference_total: apiData.difference,
        len_teams: teams.length
    };
}

// Calculate team skills totals and averages
function calculateTeamSkills(teamPlayers) {
    const teamSkills = {
        "velocidad": {"total": 0, "avg": 0},
        "resistencia": {"total": 0, "avg": 0},
        "control": {"total": 0, "avg": 0},
        "pases": {"total": 0, "avg": 0},
        "tiro": {"total": 0, "avg": 0},
        "defensa": {"total": 0, "avg": 0},
        "habilidad_arquero": {"total": 0, "avg": 0},
        "fuerza_cuerpo": {"total": 0, "avg": 0},
        "vision": {"total": 0, "avg": 0}
    };
    
    // Sum all skills
    teamPlayers.forEach(player => {
        Object.keys(teamSkills).forEach(skill => {
            teamSkills[skill]["total"] += player[skill] || 0;
        });
    });
    
    // Calculate averages
    const numPlayers = teamPlayers.length;
    Object.keys(teamSkills).forEach(skill => {
        teamSkills[skill]["avg"] = String(Math.round((teamSkills[skill]["total"] / numPlayers) * 100) / 100).replace(".", ",");
    });
    
    // Calculate total skills
    const totalSkills = Object.values(teamSkills).reduce((sum, skill) => sum + skill["total"], 0);
    const avgSkills = String(Math.round((totalSkills / numPlayers) * 100) / 100).replace(".", ",");
    
    return [teamSkills, totalSkills, avgSkills];
}

// Display the teams results using the results template format
function displayTeamsResults(data) {
    const resultsContainer = document.getElementById('teams-results');
    
    // Generate HTML similar to results.html template
    let html = `<div class="results-section">`;
    
    // Generate team options
    for (let i = 0; i < data.len_teams - 1; i += 2) {
        const optionNumber = Math.floor(i / 2) + 1;
        
        if (data.len_teams > 2) {
            html += `<h2>Opción ${optionNumber}</h2>`;
        }
        
        html += `
            <div class="team-container" id="resultados-equipos${optionNumber}">
                <div class="team">
                    <h2>Equipo 1</h2>
                    <ul class="team-list" data-index="${i}">
        `;
        
        // Add team 1 players
        data.teams[i][0].forEach((player, index) => {
            html += `
                <li class="player-item">
                    <span class="player-number">${index + 1}.</span>
                    <span class="player-name">${player}</span>
                    <button type="button" class="swap-button" onclick="swapPlayer('${player}', '${i}', '${i + 1}')"><i class="fa-solid fa-right-left"></i></button>
                </li>
            `;
        });
        
        html += `
                    </ul>
                </div>
                <div class="team">
                    <h2>Equipo 2</h2>
                    <ul class="team-list" data-index="${i + 1}">
        `;
        
        // Add team 2 players
        data.teams[i + 1][0].forEach((player, index) => {
            html += `
                <li class="player-item">
                    <span class="player-number">${index + 1}.</span>
                    <span class="player-name">${player}</span>
                    <button type="button" class="swap-button" onclick="swapPlayer('${player}', '${i + 1}', '${i}')"><i class="fa-solid fa-right-left"></i></button>
                </li>
            `;
        });
        
        html += `
                    </ul>
                </div>
                <div class="stats-container">
                    <div class="button-container">
                        <button type="button" id="mostrarDetalles${optionNumber}" onclick="toggleStats(this)">
                            <i class="fas fa-chart-bar" style="padding-right: 5px;"></i>
                            <span>Mostrar detalles</span>
                        </button>
                        <button type="button" id="shareButton${optionNumber}" onclick="compartirEquipos(this)">
                            <i class="fas fa-share" style="padding-right: 5px;"></i> Enviar equipos
                        </button>
                        <button type="button" id="generarFormaciones${optionNumber}" onclick="generarFormaciones(this)">
                            <i class="fa-solid fa-wand-magic-sparkles" style="padding-right: 5px;"></i>
                            Generar formaciones
                        </button>
                    </div>
                    <div class="content-container" id="content-container${optionNumber}" data-players-count="${data.teams[i][0].length}" style="display: none;">
                        <!-- Carousel nativo -->
                        <div class="carousel-container">
                            <div class="carousel-slides">
                                <div class="carousel-slide">
                                    <div class="table-container">
                                        <table id="skills-table${optionNumber}">
                                            <thead>
                                                <tr>
                                                    <th>Habilidad</th>
                                                    <th>Equipo 1</th>
                                                    <th>Equipo 2</th>
                                                </tr>
                                            </thead>
                                            <tbody>
        `;
        
        // Add skills rows
        Object.entries(data.skills).forEach(([key, value]) => {
            html += `
                <tr>
                    <td>${value}</td>
                    <td>${data.teams[i][1][0][key]["total"]}</td>
                    <td>${data.teams[i + 1][1][0][key]["total"]}</td>
                </tr>
            `;
        });
        
        html += `
                                                <tr>
                                                    <td>Total</td>
                                                    <td>${data.teams[i][1][1]}</td>
                                                    <td>${data.teams[i + 1][1][1]}</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                <div class="carousel-slide">
                                    <div class="chart-container">
                                        <canvas></canvas>
                                    </div>
                                </div>
                                <div class="carousel-slide formation-slide">
                                    <div class="formation-wrapper" id="formation-wrapper${optionNumber}">
                                        <div class="formation-placeholder" id="formation-placeholder${optionNumber}">
                                            <p>Generá la formación para verla acá.</p>
                                            <p>Usá el botón "Generar formaciones".</p>
                                        </div>
                                        <div class="field-container" id="formations-container${optionNumber}" style="display: none;">
                                            <div id="soccer-field${optionNumber}" class="soccer-field">
                                                <!-- Players will be positioned here -->
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <button class="carousel-btn carousel-prev">❮</button>
                            <button class="carousel-btn carousel-next">❯</button>
                        </div>
                    </div>
                </div>
            </div>
            <hr>
        `;
    }
    
    html += '</div>';
    
    // Set the HTML and show the results
    resultsContainer.innerHTML = html;
    resultsContainer.style.display = 'block';
    hasResults = true; // Marcar que hay resultados generados
    
    // Scroll to results
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Initialize carousel components for the results view
    if (typeof createCarousel === 'function') {
        const carousels = resultsContainer.querySelectorAll('.carousel-container');
        carousels.forEach(carousel => createCarousel(carousel));
    }
}

// ==================== IMPORT PLAYERS MODAL ====================
let importMatchResults = null; // Almacena los resultados del matching

function initImportModal() {
    const modal = document.getElementById('import-modal');
    const importBtn = document.getElementById('import-players-btn');
    const closeBtn = document.getElementById('close-import-modal');
    const cancelBtn = document.getElementById('cancel-import-btn');
    const processBtn = document.getElementById('process-import-btn');
    const applyBtn = document.getElementById('apply-import-btn');
    
    if (!modal) return;
    
    // Event listeners
    importBtn?.addEventListener('click', showImportModal);
    closeBtn?.addEventListener('click', closeImportModal);
    cancelBtn?.addEventListener('click', closeImportModal);
    processBtn?.addEventListener('click', processImportList);
    applyBtn?.addEventListener('click', applyImportedPlayers);
    
    // Cerrar al hacer click fuera del modal
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeImportModal();
        }
    });
    
    // Cerrar con Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeImportModal();
        }
    });
}

function showImportModal() {
    const modal = document.getElementById('import-modal');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Reset modal state
    resetImportModal();
}

function closeImportModal() {
    const modal = document.getElementById('import-modal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
    
    // Reset state
    resetImportModal();
}

function resetImportModal() {
    const textarea = document.getElementById('import-players-textarea');
    const resultsDiv = document.getElementById('import-results');
    const processBtn = document.getElementById('process-import-btn');
    const applyBtn = document.getElementById('apply-import-btn');
    
    if (textarea) textarea.value = '';
    if (resultsDiv) resultsDiv.style.display = 'none';
    if (processBtn) processBtn.style.display = 'flex';
    if (applyBtn) applyBtn.style.display = 'none';
    
    importMatchResults = null;
}

async function processImportList() {
    const textarea = document.getElementById('import-players-textarea');
    const processBtn = document.getElementById('process-import-btn');
    const resultsDiv = document.getElementById('import-results');
    const matchesDiv = document.getElementById('import-matches');
    const notFoundDiv = document.getElementById('import-not-found');
    const applyBtn = document.getElementById('apply-import-btn');
    
    const text = textarea.value.trim();
    
    if (!text) {
        alert('Por favor, ingresá una lista de nombres de jugadores');
        return;
    }
    
    // Parse names from text (handle both commas and newlines)
    const inputNames = text
        .split(/[\n,]+/)
        .map(name => name.trim())
        .filter(name => name.length > 0);
    
    if (inputNames.length === 0) {
        alert('No se encontraron nombres válidos en la lista');
        return;
    }
    
    // Limit check (matches backend MAX_LINES)
    if (inputNames.length > MAX_IMPORT_LINES) {
        alert(`Se permiten máximo ${MAX_IMPORT_LINES} líneas. Por favor, reduce la lista.`);
        return;
    }
    
    // Show loading state
    processBtn.disabled = true;
    processBtn.innerHTML = '<span class="spinner"></span> Buscando...';
    resultsDiv.style.display = 'block';
    matchesDiv.innerHTML = '<div class="import-loading"><div class="spinner"></div>Buscando coincidencias con IA...</div>';
    notFoundDiv.style.display = 'none';
    
    try {
        // Build request data
        const requestData = {
            input_names: inputNames,
            scale: currentScale === 5 ? '1-5' : '1-10'
        };
        
        // Add club_id if using a club context
        const clubId = getCurrentClubId();
        if (clubId !== 'my-players') {
            requestData.club_id = parseInt(clubId);
        }
        
        // Call API
        const response = await fetch('/api/match-players', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al buscar coincidencias');
        }
        
        const data = await response.json();
        importMatchResults = data;
        
        // Render results
        renderImportResults(data);
        
        // Show apply button if there are matches
        if (data.matches && data.matches.length > 0) {
            processBtn.style.display = 'none';
            applyBtn.style.display = 'flex';
        }
        
    } catch (error) {
        console.error('Error processing import:', error);
        matchesDiv.innerHTML = `<div style="color: #ff6b6b; padding: 20px; text-align: center;">
            ❌ ${error.message}
        </div>`;
    } finally {
        processBtn.disabled = false;
        processBtn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Buscar coincidencias';
    }
}

function renderImportResults(data) {
    const matchesDiv = document.getElementById('import-matches');
    const notFoundDiv = document.getElementById('import-not-found');
    const notFoundList = document.getElementById('not-found-list');
    
    // Clear previous results
    matchesDiv.innerHTML = '';
    
    // Render matches
    if (data.matches && data.matches.length > 0) {
        data.matches.forEach((match, index) => {
            const confidenceClass = match.confidence === 'low' ? 'low-confidence' : '';
            const matchItem = document.createElement('div');
            matchItem.className = `import-match-item ${confidenceClass}`;
            matchItem.innerHTML = `
                <div class="import-match-info">
                    <span class="import-match-input">"${escapeHTML(match.input_name)}" →</span>
                    <span class="import-match-result">${escapeHTML(match.matched_player_name)}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="import-match-confidence ${match.confidence}">${getConfidenceLabel(match.confidence)}</span>
                    <input type="checkbox" class="import-match-checkbox" data-player-id="${match.matched_player_id}" data-player-name="${escapeHTML(match.matched_player_name)}" checked>
                </div>
            `;
            matchesDiv.appendChild(matchItem);
        });
    } else {
        matchesDiv.innerHTML = '<div style="color: #999; padding: 20px; text-align: center;">No se encontraron coincidencias</div>';
    }
    
    // Render not found
    if (data.not_found && data.not_found.length > 0) {
        notFoundDiv.style.display = 'block';
        notFoundList.innerHTML = '';
        data.not_found.forEach(name => {
            const li = document.createElement('li');
            li.textContent = name;
            notFoundList.appendChild(li);
        });
    } else {
        notFoundDiv.style.display = 'none';
    }
}

function getConfidenceLabel(confidence) {
    switch (confidence) {
        case 'high': return '✓ Seguro';
        case 'medium': return '~ Probable';
        case 'low': return '? Posible';
        default: return confidence;
    }
}

function applyImportedPlayers() {
    // Get all checked matches
    const checkboxes = document.querySelectorAll('.import-match-checkbox:checked');
    
    if (checkboxes.length === 0) {
        alert('No hay jugadores seleccionados para agregar');
        return;
    }
    
    // If there is an existing selection, confirm replacement
    if (selectedPlayers.size > 0) {
        const shouldReplace = window.confirm(
            'Ya tenés jugadores seleccionados manualmente.\n' +
            'Al aplicar la importación se va a reemplazar la selección actual por los jugadores importados.\n\n' +
            '¿Querés continuar y reemplazar la selección actual?'
        );
        
        if (!shouldReplace) {
            return;
        }
    }
    
    // Clear current selection
    selectedPlayers.clear();
    
    // Add matched players to selection
    checkboxes.forEach(checkbox => {
        const playerName = checkbox.dataset.playerName;
        if (playerName) {
            selectedPlayers.add(playerName);
        }
    });
    
    // Render updated player list
    renderPlayers();
    
    // Close modal
    closeImportModal();
    
    // Show success message
    const count = selectedPlayers.size;
    const notFoundCount = importMatchResults?.not_found?.length || 0;
    
    let message = `✅ Se seleccionaron ${count} jugador${count !== 1 ? 'es' : ''}`;
    if (notFoundCount > 0) {
        message += `\n⚠️ ${notFoundCount} nombre${notFoundCount !== 1 ? 's' : ''} no ${notFoundCount !== 1 ? 'fueron encontrados' : 'fue encontrado'}`;
    }
    
    alert(message);
}
// ==================== END IMPORT PLAYERS MODAL ====================

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', init);