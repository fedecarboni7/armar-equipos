// ========================================
// CLUB SELECTOR - Módulo Común
// ========================================
// Este archivo contiene todas las funciones relacionadas con el selector de club
// para evitar duplicación entre players.js, armar_equipos.js, etc.

// Variables globales para el contexto de club
let currentClubId = 'my-players';
let userClubs = [];

// ========================================
// CARGA DE DATOS
// ========================================

// Cargar clubes del usuario
async function loadUserClubs() {
    try {
        const response = await fetch('/api/user-clubs', {
            method: 'GET',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            userClubs = await response.json();
            populateClubSelector();
        } else {
            console.error('Error loading user clubs:', response.status);
            // Si falla, al menos mantener "Mis jugadores"
            populateClubSelector();
        }
    } catch (error) {
        console.error('Error loading user clubs:', error);
        // Si falla, al menos mantener "Mis jugadores"
        populateClubSelector();
    }
}

// ========================================
// INTERFAZ DE USUARIO
// ========================================

// Poblar el selector de clubes
function populateClubSelector() {
    const selector = document.getElementById('club-select-navbar');
    if (!selector) return; // Si no existe el selector en esta página, salir
    
    // Limpiar opciones existentes excepto "Mis jugadores"
    selector.innerHTML = '<option value="my-players">Mis jugadores</option>';
    
    // Agregar clubes del usuario
    userClubs.forEach(club => {
        const option = document.createElement('option');
        option.value = club.id;
        option.textContent = club.name;
        selector.appendChild(option);
    });
    
    // Cargar la selección guardada desde localStorage
    const savedClubId = localStorage.getItem('selectedClubId');
    if (savedClubId && (savedClubId === 'my-players' || userClubs.some(club => club.id == savedClubId))) {
        currentClubId = savedClubId;
        selector.value = savedClubId;
    }
    
    // Actualizar icono según contexto actual
    updateContextIcon();
}

// Actualizar el icono según el contexto actual
function updateContextIcon() {
    const contextIcon = document.getElementById('contextIcon');
    if (!contextIcon) return;
    
    const selector = document.getElementById('club-select-navbar');
    if (!selector) return;
    
    if (selector.value === 'my-players') {
        contextIcon.textContent = '👤'; // Icono de usuario personal
    } else {
        contextIcon.textContent = '⚽'; // Icono de club
    }
}

// ========================================
// CAMBIO DE CONTEXTO
// ========================================

// Cambiar contexto (club o personal)
async function switchContext() {
    const selector = document.getElementById('club-select-navbar');
    const selectedValue = selector.value;
    
    // Mostrar feedback visual mientras cambia el contexto
    const originalText = selector.options[selector.selectedIndex].text;
    selector.disabled = true;
    
    try {
        currentClubId = selectedValue;
        
        // Guardar la selección en localStorage para persistencia entre páginas
        localStorage.setItem('selectedClubId', selectedValue);
        
        updateContextIcon();
        
        // Llamar a la función específica de cada página si existe
        if (typeof onContextChanged === 'function') {
            await onContextChanged(selectedValue);
        }
        
        // Mostrar mensaje de éxito brevemente
        const contextInfo = selectedValue === 'my-players' ? 'Mis jugadores' : 
                          userClubs.find(club => club.id == selectedValue)?.name || 'Club desconocido';
        
    } catch (error) {
        // Si hay error, restaurar la selección anterior y mostrar error
        console.error('Error switching context:', error);
        showError('Error al cambiar el contexto. Intentá de nuevo.');
    } finally {
        selector.disabled = false;
    }
}

// ========================================
// CREAR CLUB - MODAL Y FUNCIONALIDAD
// ========================================

// Abrir modal de creación de club
function openCreateClubModal() {
    const modal = document.getElementById('createClubModal');
    const input = document.getElementById('new-club-name');
    
    if (modal && input) {
        modal.classList.add('active');
        input.value = ''; // Limpiar el campo
        setTimeout(() => input.focus(), 100); // Enfocar en el campo de nombre
    } else {
        console.error('Modal de crear club no encontrado en esta página');
        alert('Funcionalidad no disponible en esta página');
    }
}

// Cerrar modal de creación de club
function closeCreateClubModal() {
    const modal = document.getElementById('createClubModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

// Función genérica para abrir modal (compatibilidad con index.html)
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

// Función genérica para cerrar modal (compatibilidad con index.html)  
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Crear nuevo club
async function createNewClub() {
    const clubNameInput = document.getElementById('new-club-name');
    if (!clubNameInput) {
        console.error('Campo de nombre de club no encontrado');
        return;
    }
    
    const clubName = clubNameInput.value.trim();
    if (!clubName || clubName.length < 2) {
        alert("Por favor, ingresa un nombre válido para el club (mínimo 2 caracteres).");
        clubNameInput.focus();
        return;
    }
    
    try {
        // Deshabilitar el botón mientras se crea
        const createButton = document.querySelector('#createClubModal .btn-primary');
        if (createButton) {
            createButton.disabled = true;
            createButton.textContent = 'Creando...';
        }
        
        // Hacer la solicitud para crear el club
        const response = await fetch('/clubs/', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: clubName }),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al crear el club');
        }
        
        const newClub = await response.json();
        
        // Agregar el nuevo club a la lista local
        userClubs.push(newClub);
        
        // Actualizar el selector
        populateClubSelector();
        
        // Cambiar al nuevo club
        const selector = document.getElementById('club-select-navbar');
        if (selector) {
            selector.value = newClub.id;
            currentClubId = newClub.id;
            
            // Guardar la selección en localStorage para persistencia
            localStorage.setItem('selectedClubId', newClub.id);
            
            updateContextIcon();
            
            // Llamar a la función específica de cada página si existe
            if (typeof onContextChanged === 'function') {
                await onContextChanged(newClub.id);
            }
        }
        
        // Cerrar modal
        closeCreateClubModal();
        
        // Mostrar mensaje de éxito
        showSuccessMessage(`✓ Club "${clubName}" creado exitosamente`);
        
    } catch (error) {
        console.error('Error creating club:', error);
        alert('Error al crear el club: ' + error.message);
    } finally {
        // Restaurar el botón
        const createButton = document.querySelector('#createClubModal .btn-primary');
        if (createButton) {
            createButton.disabled = false;
            createButton.textContent = 'Crear';
        }
    }
}

// ========================================
// UTILIDADES
// ========================================

// Función común para mostrar errores
function showError(message) {
    console.error(message);
    // Crear un toast de error
    showToast(message, 'error');
}

// Función común para mostrar mensajes de éxito
function showSuccessMessage(message) {
    showToast(message, 'success');
}

// Función para mostrar toasts/notificaciones
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#28a745' : '#dc3545';
    
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: ${bgColor};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 10000;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        transform: translateX(100px);
        opacity: 0;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Animar entrada
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity = '1';
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

// ========================================
// EVENTOS GLOBALES
// ========================================

// Cerrar modales al hacer clic fuera
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
});

// Manejar tecla Escape para cerrar modales
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const activeModal = document.querySelector('.modal.active');
        if (activeModal) {
            activeModal.classList.remove('active');
        }
    }
});

// ========================================
// INICIALIZACIÓN
// ========================================

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Solo cargar clubes si hay un selector en la página
    if (document.getElementById('club-select-navbar')) {
        loadUserClubs().then(() => {
            // Después de cargar los clubes, verificar si hay un club guardado
            const savedClubId = localStorage.getItem('selectedClubId');
            if (savedClubId && savedClubId !== 'my-players') {
                // Verificar si el club guardado aún existe
                const clubExists = userClubs.some(club => club.id == savedClubId);
                if (clubExists && typeof onContextChanged === 'function') {
                    // Si el club existe, aplicar el cambio de contexto
                    onContextChanged(savedClubId);
                } else if (!clubExists) {
                    // Si el club ya no existe, resetear a "mis jugadores" y limpiar localStorage
                    localStorage.removeItem('selectedClubId');
                    currentClubId = 'my-players';
                    const selector = document.getElementById('club-select-navbar');
                    if (selector) {
                        selector.value = 'my-players';
                        updateContextIcon();
                    }
                }
            }
        });
    }
});

// ========================================
// FUNCIONES DE INTEGRACIÓN PARA PÁGINAS ESPECÍFICAS
// ========================================

// Función que cada página puede definir para manejar cambios de contexto
// Por ejemplo: en players.js se definiría como:
// function onContextChanged(contextId) { return loadPlayersForContext(contextId); }

// Funciones para obtener el estado actual (para uso en otras páginas)
function getCurrentClubId() {
    return currentClubId;
}

function getUserClubs() {
    return [...userClubs]; // Retornar copia para evitar modificaciones accidentales
}

function setCurrentClubId(clubId) {
    currentClubId = clubId;
    const selector = document.getElementById('club-select-navbar');
    if (selector) {
        selector.value = clubId;
        updateContextIcon();
    }
}