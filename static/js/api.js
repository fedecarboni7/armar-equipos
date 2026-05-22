// Variables globales para datos de jugadores y equipos 
window.playerDataDict = {};
window.teams = {};

// Global scale utilities — shared across all pages
function getCurrentScale() {
    return parseInt(localStorage.getItem('selectedScale') || '5', 10);
}

function setCurrentScale(scale) {
    localStorage.setItem('selectedScale', String(scale));
}

// Single global setScale — used by _scale_selector.html onclick on every page
window.setScale = function (scale) {
    setCurrentScale(scale);

    const buttons = document.querySelectorAll('.scale-option');
    buttons.forEach((btn) => btn.classList.remove('active'));
    const index = scale === 5 ? 0 : 1;
    if (buttons[index]) {
        buttons[index].classList.add('active');
    }

    document.dispatchEvent(new CustomEvent('scaleChanged', { detail: { scale } }));
};

// Restore active button on load
document.addEventListener('DOMContentLoaded', function () {
    const stored = getCurrentScale();
    const index = stored === 5 ? 0 : 1;
    const buttons = document.querySelectorAll('.scale-option');
    buttons.forEach((btn) => btn.classList.remove('active'));
    if (buttons[index]) {
        buttons[index].classList.add('active');
    }
});

// API utilities for teams builder
class TeamsAPI {
    static async get(url) {
        try {
            const response = await fetch(url, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Error del servidor' }));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    }

    static async post(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Error del servidor' }));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    }

    static async getPlayers(clubId = null, scale = '1-5') {
        let url = `/api/players?scale=${scale}`;
        if (clubId) {
            url += `&club_id=${clubId}`;
        }
        return await this.get(url);
    }

    static async buildTeams(selectedPlayerIds, clubId = null, scale = '1-5') {
        const requestBody = {
            selected_player_ids: selectedPlayerIds,
            scale: scale
        };
        
        if (clubId) {
            requestBody.club_id = parseInt(clubId);
        }
        
        return await this.post('/api/build-teams', requestBody);
    }
}

// Generar formaciones
function generarFormaciones(button) {
    const indice = button.id.replace('generarFormaciones', ''); // Obtiene el índice del botón

    // Validar y preparar los datos usando la función de teamLogic.js
    const payload = validateAndPrepareTeamsForFormations(indice);
    if (!payload) {
        return; // La validación falló
    }

    const formationsContainer = document.getElementById('formations-container' + indice);
    const formationPlaceholder = document.getElementById('formation-placeholder' + indice);
    if (formationPlaceholder) {
        formationPlaceholder.style.display = 'flex';
        formationPlaceholder.innerHTML = '<p>Generá la formación para verla acá.</p><p>Usá el botón "Generar formaciones".</p>';
    }
    if (formationsContainer) {
        formationsContainer.style.display = 'none';
    }

    // Crear el spinner y agregarlo al botón
    const spinner = document.createElement('span');
    spinner.className = 'spinner';
    button.appendChild(spinner);

    // Deshabilitar el botón para prevenir múltiples clics
    button.disabled = true;

    // Enviar la solicitud usando fetch
    fetch('/formations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',  // Enviar como JSON
        },
        body: JSON.stringify(payload),  // Serializar el objeto completo como JSON
    })
    .then(response => response.json())  // Cambiar a .json() si el backend responde con JSON
    .then(data => {
        if (button.contains(spinner)) {
            button.removeChild(spinner);
        }

        positionPlayers(data, indice);  // Procesar los datos de las formaciones
        
        // Mostrar el contenedor de formaciones
        if (formationPlaceholder) {
            formationPlaceholder.style.display = 'none';
        }
        if (formationsContainer) {
            formationsContainer.style.display = 'flex';
        }
        
        // Cambiar el estilo del botón para indicar que ya no está activo
        button.style.backgroundColor = "#777";
        button.style.cursor = "not-allowed";
        button.innerText = "Formación generada";

        const contentContainer = document.getElementById('content-container' + indice);
        const detallesButton = document.getElementById('mostrarDetalles' + indice);

        if (contentContainer) {
            const isHidden = contentContainer.style.display === 'none' || contentContainer.style.display === '';

            if (isHidden && detallesButton) {
                toggleStats(detallesButton);
            } else {
                const existingCarousel = contentContainer.querySelector('.carousel-container');
                if (existingCarousel) {
                    createCarousel(existingCarousel);
                }
            }

            const carouselContainer = contentContainer.querySelector('.carousel-container');
            if (carouselContainer) {
                if (typeof window.goToCarouselSlide === 'function') {
                    window.goToCarouselSlide(carouselContainer, 2);
                } else if (typeof carouselContainer.goToSlide === 'function') {
                    carouselContainer.goToSlide(2);
                }
            }
        }
    })
    .catch(error => {
        console.error('Error fetching formations:', error);
        if (formationsContainer) {
            formationsContainer.style.display = 'none';
        }
        if (formationPlaceholder) {
            formationPlaceholder.style.display = 'flex';
            formationPlaceholder.innerHTML = '<p>No pudimos generar la formación.</p><p>Intentalo de nuevo en un momento.</p>';
        }
        if (button.contains(spinner)) {
            button.removeChild(spinner);
        }
        button.disabled = false;
    })
    .finally(() => {
        if (button.contains(spinner)) {
            button.removeChild(spinner);
        }
    });
}
