// Configuración de escala
let currentScale = 5;

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
            'Intenta con otro término de búsqueda' :
            '¡Agrega tu primer jugador para comenzar!';
        
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
        
        const initial = player.name.charAt(0).toUpperCase();
        const score = calculateAverage(player);
        const lastModified = player.updated_at;
        
        playerRow.innerHTML = `
            <div class="player-name">
                <div class="player-initial">${initial}</div>
                <div class="player-full-name">${player.name}</div>
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

// Función para cambiar escala
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

// Función para renderizar el modal del jugador
// Function to handle avatar image load errors
function handleAvatarImageError(imgElement) {
    imgElement.style.display = 'none';
    const fallbackElement = imgElement.nextElementSibling;
    if (fallbackElement && fallbackElement.classList.contains('avatar-initials')) {
        fallbackElement.style.display = 'flex';
    }
}

// Maximum file size for photo upload (500KB)
const MAX_PHOTO_SIZE = 500 * 1024;

// Variable to store the pending photo data during edit/create
let pendingPhotoData = null;

// Function to validate base64 image data
function isValidBase64Image(data) {
    if (!data || typeof data !== 'string') {
        return false;
    }
    // Check if it's a valid data URI for an image
    const validPrefixes = [
        'data:image/jpeg;base64,',
        'data:image/png;base64,',
        'data:image/gif;base64,',
        'data:image/webp;base64,',
        'data:image/svg+xml;base64,',
        'data:image/bmp;base64,'
    ];
    return validPrefixes.some(prefix => data.startsWith(prefix));
}

// Function to handle photo file selection
function handlePhotoFileSelect(event, previewId) {
    const file = event.target.files[0];
    const preview = document.getElementById(previewId);
    const removeBtn = document.getElementById(previewId + '-remove');
    
    if (!file) {
        return;
    }
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('Por favor selecciona un archivo de imagen válido (JPG, PNG, GIF, etc.)');
        event.target.value = '';
        return;
    }
    
    // Validate file size
    if (file.size > MAX_PHOTO_SIZE) {
        alert(`La imagen es muy grande. El tamaño máximo es ${MAX_PHOTO_SIZE / 1024}KB. Tu archivo tiene ${Math.round(file.size / 1024)}KB.`);
        event.target.value = '';
        return;
    }
    
    // Read file as base64
    const reader = new FileReader();
    reader.onload = function(e) {
        const result = e.target.result;
        // Validate the result is a proper base64 image
        if (isValidBase64Image(result)) {
            pendingPhotoData = result;
            if (preview) {
                preview.src = pendingPhotoData;
                preview.style.display = 'block';
            }
            if (removeBtn) {
                removeBtn.style.display = 'inline-block';
            }
        } else {
            alert('El archivo no es una imagen válida.');
            event.target.value = '';
        }
    };
    reader.readAsDataURL(file);
}

// Function to remove selected photo
function removeSelectedPhoto(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const removeBtn = document.getElementById(previewId + '-remove');
    
    pendingPhotoData = null;
    if (input) input.value = '';
    if (preview) {
        preview.src = '';
        preview.style.display = 'none';
    }
    if (removeBtn) {
        removeBtn.style.display = 'none';
    }
}

function renderPlayerModal(player) {
    const details = document.getElementById('player-details');
    const average = calculateAverage(player);
    const lastModified = player.updated_at;
    const initial = player.name.charAt(0).toUpperCase();
    
    // Reset pending photo data and set it to current player's photo (only if valid)
    const hasValidPhoto = player.photo_data && isValidBase64Image(player.photo_data);
    pendingPhotoData = hasValidPhoto ? player.photo_data : null;
    
    // Generate avatar content - show photo if available and valid, otherwise show initials
    const avatarContent = hasValidPhoto
        ? `<img src="${player.photo_data}" alt="${escapeHTML(player.name)}" class="avatar-image" data-avatar-image="true" /><div class="avatar-initials" style="display: none;">${initial}</div>`
        : `<div class="avatar-initials">${initial}</div>`;

    details.innerHTML = `
        <div class="player-detail-header">
            <div class="player-detail-avatar">
                ${avatarContent}
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
                <label>Foto de Perfil (opcional, máx. 500KB)</label>
                <div class="photo-upload-container">
                    <input type="file" id="edit-photo-file" accept="image/*" onchange="handlePhotoFileSelect(event, 'edit-photo-preview')" />
                    <div class="photo-preview-container">
                        <img id="edit-photo-preview" class="photo-preview" src="${hasValidPhoto ? player.photo_data : ''}" style="display: ${hasValidPhoto ? 'block' : 'none'};" />
                        <button type="button" id="edit-photo-preview-remove" class="btn-remove-photo" style="display: ${hasValidPhoto ? 'inline-block' : 'none'};" onclick="removeSelectedPhoto('edit-photo-file', 'edit-photo-preview')">✕ Quitar foto</button>
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
        
        // Attach error handler to avatar image if present
        const avatarImage = details.querySelector('[data-avatar-image="true"]');
        if (avatarImage) {
            avatarImage.addEventListener('error', function() {
                handleAvatarImageError(this);
            });
        }
        
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

// Función para mostrar mensaje de éxito
function showSuccessMessage(message) {
    // Crear un toast o mensaje temporal
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #28a745;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 10000;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Animar entrada
    setTimeout(() => {
        toast.style.transform = 'translateX(-10px)';
    }, 100);
    
    // Remover después de 3 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => {
            if (toast.parentNode) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, 3000);
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
            photo_data: pendingPhotoData,
            ...skillValues,
            club_id: currentEditingPlayer.club_id || null
        };

        await savePlayer(playerData);
        
        // Actualizar el jugador actual con los nuevos datos
        Object.assign(currentEditingPlayer, playerData);
        
        // Mostrar mensaje de éxito
        showSuccessMessage('✓ Jugador guardado exitosamente');
        
        // Cambiar a modo vista sin cerrar el modal
        isEditMode = false;
        renderPlayerModal(currentEditingPlayer);
        
    } catch (error) {
        alert('Error al guardar los cambios: ' + error.message);
    }
}

// Función para eliminar jugador desde el modal
async function deletePlayerFromModal(id) {
    const player = players.find(p => p.id === id);
    if (player && confirm(`¿Estás seguro de que quieres eliminar a ${player.name}?`)) {
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
    
    // Resetear modo de edición
    isEditMode = false;
    currentEditingPlayer = null;
    
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
    
    // Reset pending photo data
    pendingPhotoData = null;
    
    // Valores por defecto según la escala
    const defaultValue = currentScale === 5 ? 3 : 5;
    
    formContainer.innerHTML = `
        <div class="form-group">
            <label for="create-player-name">Nombre del Jugador</label>
            <input type="text" id="create-player-name" placeholder="Ingresa el nombre del jugador" required />
        </div>
        
        <div class="form-group">
            <label>Foto de Perfil (opcional, máx. 500KB)</label>
            <div class="photo-upload-container">
                <input type="file" id="create-photo-file" accept="image/*" onchange="handlePhotoFileSelect(event, 'create-photo-preview')" />
                <div class="photo-preview-container">
                    <img id="create-photo-preview" class="photo-preview" style="display: none;" />
                    <button type="button" id="create-photo-preview-remove" class="btn-remove-photo" style="display: none;" onclick="removeSelectedPhoto('create-photo-file', 'create-photo-preview')">✕ Quitar foto</button>
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
        photo_data: pendingPhotoData,
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