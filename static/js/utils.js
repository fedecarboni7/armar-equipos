// Función para escapar HTML especial en cadenas (prevención XSS)
function escapeHTML(str) {
    return String(str).replace(/[&<>"'`=\/]/g, function (s) {
        const entityMap = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
            '`': '&#96;',
            '=': '&#61;',
            '/': '&#47;'
        };
        return entityMap[s] || s;
    });
}

// Aplicar funcionalidad a los sliders
function applySliderEffect(container) {
    container.addEventListener('input', function(event) {
        if (event.target.classList.contains('skill-slider')) {
            const sliderRating = event.target.closest('.slider-rating');
            const hiddenInput = sliderRating.querySelector('input[type="hidden"]');
            const valueDisplay = sliderRating.querySelector('.slider-value');
            const value = event.target.value;

            hiddenInput.value = value;
            if (valueDisplay) {
                valueDisplay.textContent = value;
            }
        }
    });
}

// Mostrar u ocultar detalles de un jugador
function rotateIcon(detailsContainer, icon) {
    //wait for the animation to finish before removing the class
    detailsContainer.addEventListener('transitionend', function() {
        if (detailsContainer.style.maxHeight === "0px") {
            if (icon) {
                icon.classList.remove('rotate');
            } else {
                icon = detailsContainer.previousElementSibling.querySelector('.toggle-icon');
                icon.classList.remove('rotate');
            }
        } else {
            if (icon) {
                icon.classList.add('rotate');
            } else {
                icon = detailsContainer.previousElementSibling.querySelector('.toggle-icon');
                icon.classList.add('rotate');
            }
        }
    });
}

// Asignar un número a cada jugador agregado
function renumerarJugadores() {
    const container = document.getElementById("players-container");
    const jugadores = container.children;
    for (let i = 0; i < jugadores.length; i++) {
      const jugador = jugadores[i];
      const nameInput = jugador.querySelector(".player-header input[name='names']");
      if (nameInput && !nameInput.readOnly) {
        // Solo actualizar el placeholder si el input no es de solo lectura (jugador no guardado)
        nameInput.placeholder = "Nombre";
      }
      // Actualizar el valor del checkbox (opcional, si lo usas para algo)
      const checkbox = jugador.querySelector(".player-header input[type='checkbox']");
      if (checkbox) {
        checkbox.value = i;
      }
    }
}

// Renumerar jugadores después de un swap
function renumerarJugadoresEquipo(teamList) {
    // Obtener todos los elementos de jugador en el equipo
    const jugadores = teamList.querySelectorAll('.player-item');
    
    // Actualizar el número de cada jugador según su posición en la lista
    jugadores.forEach((jugador, index) => {
        const numeroSpan = jugador.querySelector('.player-number');
        if (numeroSpan) {
            numeroSpan.textContent = (index + 1) + '.';
        }
    });
}

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
