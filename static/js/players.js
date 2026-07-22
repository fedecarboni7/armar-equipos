// Configuración de escala
let currentScale = getCurrentScale();

// Photo upload state
let pendingPhotoFile = null;

function getPlayerType() {
    return currentScale === 5 ? 's5' : 's10';
}

function validatePhotoFile(file) {
    const maxSize = 5 * 1024 * 1024;
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];

    if (file.size > maxSize) {
        alert('La imagen no puede superar 5MB.');
        return false;
    }
    if (!allowedTypes.includes(file.type)) {
        alert('Formato no soportado. Usá JPEG, PNG o WEBP.');
        return false;
    }
    return true;
}

function setupPhotoInput(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    if (!input || !preview) return;

    input.addEventListener('change', function () {
        const file = this.files[0];
        if (!file) return;

        if (!validatePhotoFile(file)) {
            this.value = '';
            return;
        }

        pendingPhotoFile = file;
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.innerHTML = `<img class="player-avatar-img" src="${e.target.result}" width="80" height="80" />`;
        };
        reader.readAsDataURL(file);
    });
}

async function uploadPlayerPhotoIfPending(playerId) {
    if (!pendingPhotoFile) return;

    const playerType = getPlayerType();
    const formData = new FormData();
    formData.append('file', pendingPhotoFile);

    try {
        const response = await fetch(
            `/api/players/${playerType}/${playerId}/photo`,
            { method: 'POST', credentials: 'include', body: formData }
        );
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Error ${response.status}`);
        }
    } catch (error) {
        console.error('Photo upload failed:', error);
        alert('Jugador creado, pero no se pudo subir la foto: ' + error.message);
    }
}

async function removePlayerPhoto(player) {
    const playerType = getPlayerType();
    try {
        const response = await fetch(
            `/api/players/${playerType}/${player.id}/photo`,
            { method: 'DELETE', credentials: 'include' }
        );
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Error ${response.status}`);
        }
        const updated = await response.json();
        player.photo_url = updated.photo_url;

        const preview = document.getElementById('edit-photo-preview');
        if (preview) {
            preview.innerHTML = renderPlayerAvatar({ name: player.name, photo_url: null }, 80);
        }
        const removeBtn = document.getElementById('remove-photo-btn');
        if (removeBtn) removeBtn.style.display = 'none';

        showSuccessMessage('Foto eliminada');
    } catch (error) {
        console.error('Photo delete failed:', error);
        alert('Error al quitar la foto: ' + error.message);
    }
}

// ==================== HELP MODAL (Players) ====================
const HELP_MODAL_PLAYERS_KEY = 'players_helpModalShown';

function initPlayersHelpModal() {
    const modal = document.getElementById('help-modal-players');
    const helpBtn = document.getElementById('help-btn');
    const closeBtn = document.getElementById('close-help-modal-players');
    const startBtn = document.getElementById('start-btn-players');
    if (!modal) return;

    // Mostrar modal si es la primera vez
    const hasSeenHelp = localStorage.getItem(HELP_MODAL_PLAYERS_KEY);
    if (!hasSeenHelp) {
        showHelpModal();
    }

    // Event listeners
    helpBtn?.addEventListener('click', showHelpModal);
    closeBtn?.addEventListener('click', closeHelpModal);
    startBtn?.addEventListener('click', closeHelpModal);
    // Cerrar al hacer click fuera del contenido
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeHelpModal();
    });
    // Cerrar con Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) closeHelpModal();
    });

    function showHelpModal() {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeHelpModal() {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        localStorage.setItem(HELP_MODAL_PLAYERS_KEY, 'true');
    }
}
// ==================== END HELP MODAL ====================

// Variables globales
let players = [];
let filteredPlayers = []; // Nueva variable para jugadores filtrados
let searchTerm = ''; // Nueva variable para el término de búsqueda
let loading = false;

// Variables para ordenamiento
let currentSort = { column: 'name', direction: 'asc' };

// Función para formatear fecha
function formatDate(date) {
    if (typeof date === 'string') {
        date = new Date(date);
    }
    return date.toLocaleDateString('es-ES') + ' ' + date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

// Función para calcular promedio de habilidades
function calculateAverage(player) {
    const skillKeys = ['velocidad', 'resistencia', 'pases', 'tiro', 'defensa', 'fuerza_cuerpo', 'control', 'habilidad_arquero', 'vision'];
    const skillValues = skillKeys.map(key => player[key]).filter(val => typeof val === 'number');
    
    if (skillValues.length === 0) return 0;
    
    const average = skillValues.reduce((a, b) => a + b, 0) / skillValues.length;
    
    // No hacer conversión - cada tabla maneja su propia escala
    return Math.round(average * 10) / 10; // Redondear a 1 decimal
}

// Función para ordenar jugadores
function sortPlayers(column) {
    // Si ya estamos ordenando por esta columna, cambiar dirección
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        // Nueva columna, empezar con ascendente
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    
    // Aplicar ordenamiento a los jugadores filtrados
    applySortToFilteredPlayers();
    
    loading = false; // Asegurar que no esté en estado de loading
    renderPlayers();
}

// Función para cargar jugadores desde el backend
async function loadPlayers() {
    await loadPlayersForContext(getCurrentClubId());
}

// Función para filtrar jugadores por nombre
function filterPlayers() {
    const searchInput = document.getElementById('player-search');
    searchTerm = searchInput.value.toLowerCase().trim();
    
    if (searchTerm === '') {
        // Si no hay término de búsqueda, mostrar todos los jugadores
        filteredPlayers = [...players];
    } else {
        // Filtrar jugadores por nombre
        filteredPlayers = players.filter(player => 
            player.name.toLowerCase().includes(searchTerm)
        );
    }
    
    // Aplicar ordenamiento a los jugadores filtrados
    applySortToFilteredPlayers();
    renderPlayers();
}

// Función para aplicar ordenamiento a jugadores filtrados
function applySortToFilteredPlayers() {
    filteredPlayers.sort((a, b) => {
        let valueA, valueB;
        
        switch (currentSort.column) {
            case 'name':
                valueA = a.name.toLowerCase();
                valueB = b.name.toLowerCase();
                break;
            case 'score':
                valueA = calculateAverage(a);
                valueB = calculateAverage(b);
                break;
            case 'date':
                valueA = new Date(a.updated_at);
                valueB = new Date(b.updated_at);
                break;
            default:
                return 0;
        }
        
        if (valueA < valueB) {
            return currentSort.direction === 'asc' ? -1 : 1;
        }
        if (valueA > valueB) {
            return currentSort.direction === 'asc' ? 1 : -1;
        }
        return 0;
    });
}

// Función para renderizar la lista de jugadores
function renderPlayers() {
    const playersList = document.getElementById('players-list');
    
    // Actualizar indicadores de ordenamiento en el header
    updateSortIndicators();
    
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

    // Usar filteredPlayers en lugar de players
    const playersToShow = filteredPlayers.length > 0 || searchTerm === '' ? filteredPlayers : [];
    
    if (playersToShow.length === 0) {
        const contextName = getCurrentClubId() === 'my-players' ? 'personales' : 
                          getUserClubs().find(club => club.id == getCurrentClubId())?.name || 'de este club';
        
        // Mostrar mensaje diferente si es por búsqueda o por falta de jugadores
        const message = searchTerm !== '' ? 
            `🔍 No se encontraron jugadores con "${escapeHTML(searchTerm)}"` :
            `👤 No hay jugadores en ${contextName}`;
        
        const subMessage = searchTerm !== '' ?
            'Intentá con otro término de búsqueda' :
            '¡Agrega tu primer jugador para empezar!';
        
        playersList.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div style="font-size: 18px; color: #aaa; margin-bottom: 10px;">${message}</div>
                <div style="font-size: 14px; color: #666;">${subMessage}</div>
            </div>
        `;
        return;
    }

    playersToShow.forEach(player => {
        const playerRow = document.createElement('div');
        playerRow.className = 'player-row';
        playerRow.onclick = () => viewPlayer(player.id);
        
        const score = calculateAverage(player);
        const lastModified = player.updated_at;
        
        playerRow.innerHTML = `
            <div class="player-name">
                ${renderPlayerAvatar(player, 40)}
                <div class="player-full-name">${escapeHTML(player.name)}</div>
            </div>
            <div class="score">${score}/${currentScale}</div>
            <div class="last-modified">${formatDate(lastModified)}</div>
        `;
        playersList.appendChild(playerRow);
    });
}

// Función para actualizar los indicadores de ordenamiento
function updateSortIndicators() {
    // Limpiar todos los indicadores existentes
    document.querySelectorAll('.sort-indicator').forEach(indicator => {
        indicator.remove();
    });
    
    // Agregar indicador a la columna actual
    const headers = document.querySelectorAll('.table-header > div');
    let targetHeader;
    
    switch (currentSort.column) {
        case 'name':
            targetHeader = headers[0];
            break;
        case 'score':
            targetHeader = headers[1];
            break;
        case 'date':
            targetHeader = headers[2];
            break;
    }
    
    if (targetHeader) {
        const indicator = document.createElement('span');
        indicator.className = 'sort-indicator';
        indicator.textContent = currentSort.direction === 'asc' ? ' ↑' : ' ↓';
        indicator.style.color = '#007bff';
        indicator.style.fontSize = '14px';
        targetHeader.appendChild(indicator);
    }
}

document.addEventListener('scaleChanged', function (e) {
    currentScale = e.detail.scale;
    loadPlayers();
});

// Función para crear el radar chart
function createRadarChart(canvasId, playerData) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Velocidad', 'Resistencia', 'Pases', 'Tiro', 'Defensa', 'Fuerza Cuerpo', 'Control', 'Habilidad Arquero', 'Visión'],
            datasets: [{
                label: ' Puntos',
                data: [
                    playerData.velocidad,
                    playerData.resistencia,
                    playerData.pases,
                    playerData.tiro,
                    playerData.defensa,
                    playerData.fuerza_cuerpo,
                    playerData.control,
                    playerData.habilidad_arquero,
                    playerData.vision
                ],
                backgroundColor: 'rgba(200, 200, 200, 0.3)',
                borderColor: 'rgba(180, 180, 180, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(220, 220, 220, 1)',
                pointBorderColor: 'rgba(160, 160, 160, 1)',
                pointBorderWidth: 2,
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: currentScale,
                    min: 0,
                    ticks: {
                        display: false,
                        stepSize: currentScale === 5 ? 1 : 2
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.2)',
                        lineWidth: 1
                    },
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.2)',
                        lineWidth: 1
                    },
                    pointLabels: {
                        color: '#fff',
                        font: {
                            size: 13,
                            weight: '500'
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Variables para el modo de edición
let isEditMode = false;
let currentEditingPlayer = null;

// Función para ver detalles del jugador
function viewPlayer(id) {
    const player = players.find(p => p.id === id);
    if (player) {
        currentEditingPlayer = player;
        isEditMode = false;
        renderPlayerModal(player);
        document.getElementById('playerModal').style.display = 'block';
    }
}

function renderPlayerModal(player) {
    const details = document.getElementById('player-details');
    const average = calculateAverage(player);
    const lastModified = player.updated_at;

    details.innerHTML = `
        <div class="player-detail-header">
            <div class="player-detail-avatar">
                ${renderPlayerAvatar(player, 80)}
            </div>
            <div class="player-detail-info">
                <h3>${escapeHTML(player.name)}</h3>
                <p class="average-score">Promedio General: ${average}/${currentScale}</p>
                <p class="last-modified">Última Modificación: ${formatDate(lastModified)}</p>
            </div>
        </div>
        
        <div class="chart-container-modal">
            <canvas id="detail-chart-${player.id}" width="300" height="300"></canvas>
        </div>
        
        <div id="view-mode" class="view-mode" style="display: ${isEditMode ? 'none' : 'block'}">
            <div class="skills-detail-grid">
                <div class="skill-detail-item">
                    <span class="skill-detail-name">Velocidad</span>
                    <span class="skill-detail-value">${player.velocidad}/${currentScale}</span>
                </div>
                <div class="skill-detail-item">
                    <span class="skill-detail-name">Resistencia</span>
                    <span class="skill-detail-value">${player.resistencia}/${currentScale}</span>
                </div>
                <div class="skill-detail-item">
                    <span class="skill-detail-name">Pases</span>
                    <span class="skill-detail-value">${player.pases}/${currentScale}</span>
                </div>
                <div class="skill-detail-item">
                    <span class="skill-detail-name">Tiro</span>
                    <span class="skill-detail-value">${player.tiro}/${currentScale}</span>
                </div>
                <div class="skill-detail-item">
                    <span class="skill-detail-name">Defensa</span>
                    <span class="skill-detail-value">${player.defensa}/${currentScale}</span>
                </div>
                <div class="skill-detail-item">
                    <span class="skill-detail-name">Fuerza Cuerpo</span>
                    <span class="skill-detail-value">${player.fuerza_cuerpo}/${currentScale}</span>
                </div>
                <div class="skill-detail-item">
                    <span class="skill-detail-name">Control</span>
                    <span class="skill-detail-value">${player.control}/${currentScale}</span>
                </div>
                <div class="skill-detail-item">
                    <span class="skill-detail-name">Habilidad Arquero</span>
                    <span class="skill-detail-value">${player.habilidad_arquero}/${currentScale}</span>
                </div>
                <div class="skill-detail-item">
                    <span class="skill-detail-name">Visión</span>
                    <span class="skill-detail-value">${player.vision}/${currentScale}</span>
                </div>
            </div>
        </div>
        
        <div id="edit-mode" class="edit-form" style="display: ${isEditMode ? 'block' : 'none'}">
            <div class="form-group">
                <label for="edit-player-name">Nombre del Jugador</label>
                <input type="text" id="edit-player-name" value="${escapeHTML(player.name)}" />
            </div>

            <div class="form-group">
                <label>Foto del Jugador</label>
                <div class="photo-upload-container">
                    <div class="photo-preview" id="edit-photo-preview">
                        ${renderPlayerAvatar(player, 80)}
                    </div>
                    <div class="photo-upload-controls">
                        <input type="file" id="edit-photo-input" accept="image/jpeg,image/png,image/webp" hidden />
                        <button type="button" class="btn btn-secondary" onclick="document.getElementById('edit-photo-input').click()">
                            📷 Cambiar foto
                        </button>
                        ${player.photo_url ? '<button type="button" class="btn btn-danger" id="remove-photo-btn" onclick="removePlayerPhoto(currentEditingPlayer)">🗑️ Quitar foto</button>' : ''}
                        <span class="photo-upload-hint">JPEG, PNG o WEBP. Máximo 5MB.</span>
                    </div>
                </div>
            </div>
            
            <div class="form-group">
                <label>Habilidades (1-${currentScale})</label>
                <div class="skills-edit-grid">
                    <div class="skill-input">
                        <label for="edit-velocidad">Velocidad</label>
                        <input type="number" id="edit-velocidad" min="1" max="${currentScale}" value="${player.velocidad}" />
                    </div>
                    <div class="skill-input">
                        <label for="edit-resistencia">Resistencia</label>
                        <input type="number" id="edit-resistencia" min="1" max="${currentScale}" value="${player.resistencia}" />
                    </div>
                    <div class="skill-input">
                        <label for="edit-pases">Pases</label>
                        <input type="number" id="edit-pases" min="1" max="${currentScale}" value="${player.pases}" />
                    </div>
                    <div class="skill-input">
                        <label for="edit-tiro">Tiro</label>
                        <input type="number" id="edit-tiro" min="1" max="${currentScale}" value="${player.tiro}" />
                    </div>
                    <div class="skill-input">
                        <label for="edit-defensa">Defensa</label>
                        <input type="number" id="edit-defensa" min="1" max="${currentScale}" value="${player.defensa}" />
                    </div>
                    <div class="skill-input">
                        <label for="edit-fuerza_cuerpo">Fuerza Cuerpo</label>
                        <input type="number" id="edit-fuerza_cuerpo" min="1" max="${currentScale}" value="${player.fuerza_cuerpo}" />
                    </div>
                    <div class="skill-input">
                        <label for="edit-control">Control</label>
                        <input type="number" id="edit-control" min="1" max="${currentScale}" value="${player.control}" />
                    </div>
                    <div class="skill-input">
                        <label for="edit-habilidad_arquero">Habilidad Arquero</label>
                        <input type="number" id="edit-habilidad_arquero" min="1" max="${currentScale}" value="${player.habilidad_arquero}" />
                    </div>
                    <div class="skill-input">
                        <label for="edit-vision">Visión</label>
                        <input type="number" id="edit-vision" min="1" max="${currentScale}" value="${player.vision}" />
                    </div>
                </div>
            </div>
        </div>
        
        <div class="modal-actions">
            <button class="btn btn-primary" id="edit-btn" onclick="toggleEditMode()" style="display: ${isEditMode ? 'none' : 'flex'}">
                ✏️ Editar
            </button>
            <button class="btn btn-primary" id="save-btn" onclick="savePlayerEdits()" style="display: ${isEditMode ? 'flex' : 'none'}">
                💾 Guardar
            </button>
            <button class="btn btn-secondary" id="cancel-btn" onclick="cancelEdit()" style="display: ${isEditMode ? 'flex' : 'none'}">
                ❌ Cancelar
            </button>
            <button class="btn btn-danger" onclick="deletePlayerFromModal(${player.id})">
                🗑️ Eliminar
            </button>
        </div>
    `;
    
    // Crear el radar chart después de que el elemento esté en el DOM
    setTimeout(() => {
        createRadarChart(`detail-chart-${player.id}`, player);
        
        // Agregar validación en tiempo real a los inputs de habilidades
        if (isEditMode) {
            const skillInputs = ['velocidad', 'resistencia', 'pases', 'tiro', 'defensa', 'fuerza_cuerpo', 'control', 'habilidad_arquero', 'vision'];
            
            skillInputs.forEach(skill => {
                const input = document.getElementById(`edit-${skill}`);
                if (input) {
                    // Validar al cambiar el valor
                    input.addEventListener('input', function() {
                        let value = parseInt(this.value);
                        
                        // Corregir valores fuera del rango
                        if (value < 1) {
                            this.value = 1;
                        } else if (value > currentScale) {
                            this.value = currentScale;
                        }
                    });
                    
                    // Validar al perder el foco
                    input.addEventListener('blur', function() {
                        let value = parseInt(this.value);
                        
                        if (isNaN(value) || value < 1) {
                            this.value = 1;
                        } else if (value > currentScale) {
                            this.value = currentScale;
                        }
                    });
                }
            });

            pendingPhotoFile = null;
            setupPhotoInput('edit-photo-input', 'edit-photo-preview');
        }
    }, 100);
}

// Función para toggle entre modo vista y edición
function toggleEditMode() {
    isEditMode = true;
    renderPlayerModal(currentEditingPlayer);
}

// Función para cancelar la edición
function cancelEdit() {
    isEditMode = false;
    renderPlayerModal(currentEditingPlayer);
}

// Función para guardar los cambios del jugador
async function savePlayerEdits() {
    try {
        // Validar nombre
        const name = document.getElementById('edit-player-name').value.trim();
        if (!name) {
            alert('El nombre del jugador es obligatorio');
            return;
        }

        // Validar y obtener valores de habilidades
        const skillValues = {};
        const skillKeys = ['velocidad', 'resistencia', 'pases', 'tiro', 'defensa', 'fuerza_cuerpo', 'control', 'habilidad_arquero', 'vision'];
        
        for (const skill of skillKeys) {
            const value = parseInt(document.getElementById(`edit-${skill}`).value);
            
            // Validar que el valor esté en el rango correcto
            if (isNaN(value) || value < 1 || value > currentScale) {
                alert(`El valor de ${skill.replace('_', ' ')} debe estar entre 1 y ${currentScale}`);
                return;
            }
            
            skillValues[skill] = value;
        }

        const playerData = {
            id: currentEditingPlayer.id,
            name: name,
            ...skillValues,
            club_id: currentEditingPlayer.club_id || null
        };

        await savePlayer(playerData);

        // Upload photo if one was selected
        await uploadPlayerPhotoIfPending(currentEditingPlayer.id);

        // Reload to get fresh data including photo_url
        await loadPlayers();

        // Actualizar el jugador actual con los nuevos datos del servidor
        const refreshed = players.find(p => p.id === currentEditingPlayer.id);
        if (refreshed) Object.assign(currentEditingPlayer, refreshed);
        
        // Mostrar mensaje de éxito
        showSuccessMessage('✓ Jugador guardado exitosamente');
        
        // Cambiar a modo vista sin cerrar el modal
        isEditMode = false;
        pendingPhotoFile = null;
        renderPlayerModal(currentEditingPlayer);
        
    } catch (error) {
        alert('Error al guardar los cambios: ' + error.message);
    }
}

// Función para eliminar jugador desde el modal
async function deletePlayerFromModal(id) {
    const player = players.find(p => p.id === id);
    if (player && confirm(`¿Estás seguro de que querés eliminar a ${player.name}?`)) {
        try {
            const scale = currentScale === 5 ? '1-5' : '1-10';
            const response = await fetch(`/api/players/${id}?scale=${scale}`, {
                method: 'DELETE',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Error ${response.status}`);
            }
            
            closeModal();
            await loadPlayers(); // Recargar la lista
        } catch (error) {
            alert('Error al eliminar el jugador: ' + error.message);
        }
    }
}

// Función para cerrar modal
function closeModal() {
    // Limpiar cualquier chart existente
    const details = document.getElementById('player-details');
    const canvases = details.querySelectorAll('canvas');
    canvases.forEach(canvas => {
        const chart = Chart.getChart(canvas);
        if (chart) {
            chart.destroy();
        }
    });
    
    // Resetear modo de edición y photo state
    isEditMode = false;
    currentEditingPlayer = null;
    pendingPhotoFile = null;
    
    document.getElementById('playerModal').style.display = 'none';
}

// Función para agregar un jugador
function addPlayer() {
    openCreatePlayerModal();
}

// Función para abrir modal de creación de jugador
function openCreatePlayerModal() {
    const modal = document.getElementById('createPlayerModal');
    const formContainer = document.getElementById('create-player-form');
    
    // Valores por defecto según la escala
    const defaultValue = currentScale === 5 ? 3 : 5;
    
    formContainer.innerHTML = `
        <div class="form-group">
            <label for="create-player-name">Nombre del Jugador</label>
            <input type="text" id="create-player-name" placeholder="Ingresa el nombre del jugador" required />
        </div>

        <div class="form-group">
            <label>Foto del Jugador (opcional)</label>
            <div class="photo-upload-container">
                <div class="photo-preview" id="create-photo-preview">
                    <div class="player-initial" style="width:80px;height:80px;font-size:32px;">?</div>
                </div>
                <div class="photo-upload-controls">
                    <input type="file" id="create-photo-input" accept="image/jpeg,image/png,image/webp" hidden />
                    <button type="button" class="btn btn-secondary" onclick="document.getElementById('create-photo-input').click()">
                        📷 Elegir foto
                    </button>
                    <span class="photo-upload-hint">JPEG, PNG o WEBP. Máximo 5MB.</span>
                </div>
            </div>
        </div>
        
        <div class="form-group">
            <label>Habilidades (1-${currentScale})</label>
            <div class="skills-edit-grid">
                <div class="skill-input">
                    <label for="create-velocidad">Velocidad</label>
                    <input type="number" id="create-velocidad" min="1" max="${currentScale}" value="${defaultValue}" />
                </div>
                <div class="skill-input">
                    <label for="create-resistencia">Resistencia</label>
                    <input type="number" id="create-resistencia" min="1" max="${currentScale}" value="${defaultValue}" />
                </div>
                <div class="skill-input">
                    <label for="create-pases">Pases</label>
                    <input type="number" id="create-pases" min="1" max="${currentScale}" value="${defaultValue}" />
                </div>
                <div class="skill-input">
                    <label for="create-tiro">Tiro</label>
                    <input type="number" id="create-tiro" min="1" max="${currentScale}" value="${defaultValue}" />
                </div>
                <div class="skill-input">
                    <label for="create-defensa">Defensa</label>
                    <input type="number" id="create-defensa" min="1" max="${currentScale}" value="${defaultValue}" />
                </div>
                <div class="skill-input">
                    <label for="create-fuerza_cuerpo">Fuerza Cuerpo</label>
                    <input type="number" id="create-fuerza_cuerpo" min="1" max="${currentScale}" value="${defaultValue}" />
                </div>
                <div class="skill-input">
                    <label for="create-control">Control</label>
                    <input type="number" id="create-control" min="1" max="${currentScale}" value="${defaultValue}" />
                </div>
                <div class="skill-input">
                    <label for="create-habilidad_arquero">Habilidad Arquero</label>
                    <input type="number" id="create-habilidad_arquero" min="1" max="${currentScale}" value="${defaultValue}" />
                </div>
                <div class="skill-input">
                    <label for="create-vision">Visión</label>
                    <input type="number" id="create-vision" min="1" max="${currentScale}" value="${defaultValue}" />
                </div>
            </div>
        </div>
        
        <div class="modal-actions">
            <button class="btn btn-primary" onclick="saveNewPlayer()">
                💾 Crear Jugador
            </button>
            <button class="btn btn-secondary" onclick="closeCreateModal()">
                ❌ Cancelar
            </button>
        </div>
    `;
    
    // Mostrar el modal
    modal.style.display = 'block';
    
    pendingPhotoFile = null;
    setupPhotoInput('create-photo-input', 'create-photo-preview');
    
    // Agregar validación en tiempo real a los inputs
    addRealTimeValidation();
    
    // Enfocar en el campo de nombre
    setTimeout(() => {
        document.getElementById('create-player-name').focus();
    }, 100);
}

// Función para agregar validación en tiempo real
function addRealTimeValidation() {
    const skillInputs = ['velocidad', 'resistencia', 'pases', 'tiro', 'defensa', 'fuerza_cuerpo', 'control', 'habilidad_arquero', 'vision'];
    
    skillInputs.forEach(skill => {
        const input = document.getElementById(`create-${skill}`);
        if (input) {
            // Validar al cambiar el valor
            input.addEventListener('input', function() {
                let value = parseInt(this.value);
                
                // Corregir valores fuera del rango
                if (value < 1) {
                    this.value = 1;
                } else if (value > currentScale) {
                    this.value = currentScale;
                }
                
                // Eliminar clase de error si el valor es válido
                if (value >= 1 && value <= currentScale) {
                    this.classList.remove('error');
                } else {
                    this.classList.add('error');
                }
            });
            
            // Validar al perder el foco
            input.addEventListener('blur', function() {
                let value = parseInt(this.value);
                if (isNaN(value) || value < 1) {
                    this.value = 1;
                } else if (value > currentScale) {
                    this.value = currentScale;
                }
            });
        }
    });
    
    // Validación del nombre
    const nameInput = document.getElementById('create-player-name');
    if (nameInput) {
        nameInput.addEventListener('input', function() {
            if (this.value.trim().length < 2) {
                this.classList.add('error');
            } else {
                this.classList.remove('error');
            }
        });
    }
}

// Función para guardar nuevo jugador
async function saveNewPlayer() {
    const name = document.getElementById('create-player-name').value.trim();
    
    // Validar nombre
    if (!name || name.length < 2) {
        alert('Por favor ingresa un nombre válido (mínimo 2 caracteres)');
        document.getElementById('create-player-name').focus();
        return;
    }
    
    // Recopilar datos del formulario
    const playerData = {
        name: name,
        velocidad: parseInt(document.getElementById('create-velocidad').value),
        resistencia: parseInt(document.getElementById('create-resistencia').value),
        pases: parseInt(document.getElementById('create-pases').value),
        tiro: parseInt(document.getElementById('create-tiro').value),
        defensa: parseInt(document.getElementById('create-defensa').value),
        fuerza_cuerpo: parseInt(document.getElementById('create-fuerza_cuerpo').value),
        control: parseInt(document.getElementById('create-control').value),
        habilidad_arquero: parseInt(document.getElementById('create-habilidad_arquero').value),
        vision: parseInt(document.getElementById('create-vision').value)
    };
    
    // Validar todas las habilidades
    const skillKeys = ['velocidad', 'resistencia', 'pases', 'tiro', 'defensa', 'fuerza_cuerpo', 'control', 'habilidad_arquero', 'vision'];
    for (let skill of skillKeys) {
        const value = playerData[skill];
        if (isNaN(value) || value < 1 || value > currentScale) {
            alert(`La habilidad ${skill} debe estar entre 1 y ${currentScale}`);
            return;
        }
    }
    
    // Agregar club_id según el contexto
    if (getCurrentClubId() !== 'my-players') {
        playerData.club_id = getCurrentClubId();
    } else {
        playerData.club_id = null;
    }
    
    try {
        const scale = currentScale === 5 ? '1-5' : '1-10';
        const response = await fetch(`/api/player?scale=${scale}`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(playerData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Error ${response.status}`);
        }

        const newPlayer = await response.json();
        
        // Upload photo if one was selected
        if (pendingPhotoFile && newPlayer.id) {
            await uploadPlayerPhotoIfPending(newPlayer.id);
        }
        pendingPhotoFile = null;
        
        // Cerrar modal y recargar lista
        closeCreateModal();
        await loadPlayers();
        
        // Mostrar mensaje de éxito
        showSuccessMessage('Jugador creado exitosamente');
        
    } catch (error) {
        alert('Error al crear el jugador: ' + error.message);
    }
}

// Función para cerrar modal de creación
function closeCreateModal() {
    pendingPhotoFile = null;
    const modal = document.getElementById('createPlayerModal');
    modal.style.display = 'none';
}

// Función para abrir modal de edición/creación (función legacy mantenida por compatibilidad)
function openPlayerModal() {
    // Redirigir a la nueva función de creación
    openCreatePlayerModal();
}

// Función para guardar jugador
async function savePlayer(playerData) {
    const scale = currentScale === 5 ? '1-5' : '1-10';
    const response = await fetch(`/api/player?scale=${scale}`, {
        method: playerData.id ? 'PUT' : 'POST', // Usar POST para crear y PUT para editar
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(playerData)
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Error ${response.status}`);
    }
    await loadPlayers(); // Recargar la lista
}

// Cerrar modal al hacer clic fuera
window.onclick = function(event) {
    const modal = document.getElementById('playerModal');
    const createModal = document.getElementById('createPlayerModal');
    
    if (event.target === modal) {
        closeModal();
    }
    
    if (event.target === createModal) {
        closeCreateModal();
    }
}

// Variables para el contexto actual (ahora se manejan desde clubSelector.js)
// let currentClubId = 'my-players';  // Comentado - se usa desde clubSelector.js
// let userClubs = [];               // Comentado - se usa desde clubSelector.js

// Función de integración con clubSelector.js
// Esta función se llama cuando cambia el contexto desde el selector común
function onContextChanged(contextId) {
    return loadPlayersForContext(contextId);
}

// Cargar jugadores según el contexto (personal o club)
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
        players = await response.json();
        
        // Inicializar jugadores filtrados con todos los jugadores
        filteredPlayers = [...players];
        
        // Limpiar el buscador cuando cambia el contexto
        const searchInput = document.getElementById('player-search');
        if (searchInput) {
            searchInput.value = '';
            searchTerm = '';
        }
        
        // Aplicar ordenamiento actual
        if (players.length > 0) {
            applySortToFilteredPlayers();
            loading = false;
            renderPlayers();
        } else {
            loading = false;
            renderPlayers();
        }
    } catch (error) {
        loading = false;
        console.error('Error loading players for context:', error);
        players = [];
        filteredPlayers = [];
        renderPlayers(); // Mostrar error
    }
}

// Inicializar la aplicación
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar modal de ayuda
    initPlayersHelpModal();
    // El clubSelector.js se encarga de cargar los clubes automáticamente
    // Solo necesitamos cargar los jugadores
    loadPlayers();
});