// Render a player avatar circle: photo if available, else initial-letter fallback
function renderPlayerAvatar(player, size) {
    const name = player.name || '';
    const initial = name.charAt(0).toUpperCase();
    const escapedName = escapeHTML(name);
    const escapedInitial = escapeHTML(initial);

    if (player.photo_url) {
        return `<img class="player-avatar-img" src="${escapeHTML(player.photo_url)}" alt="${escapedName}" width="${size}" height="${size}" />`;
    }

    const fontSize = Math.round(size * 0.4);
    return `<div class="player-initial" style="width:${size}px;height:${size}px;font-size:${fontSize}px;">${escapedInitial}</div>`;
}

// Compartir resultados de los equipos
function compartirEquipos(button) {
    const indice = button.id.replace('shareButton', ''); // Obtiene el índice del botón
    const contenedor = document.getElementById('resultados-equipos' + indice);
    // Construye el texto a compartir
    let textoCompartir = '';
    const titulos = contenedor.querySelectorAll('h2');
    const listasJugadores = contenedor.querySelectorAll('ul');
    for (let i = 0; i < titulos.length; i++) {
        textoCompartir += '*' + titulos[i].innerText + '*\n'; // Agrega el título
        
        // Itera sobre los jugadores en la lista
        const jugadores = listasJugadores[i].querySelectorAll('li');
        for (let j = 0; j < jugadores.length; j++) {
            // Obtener solo el nombre del jugador desde el span player-name
            const playerNameElement = jugadores[j].querySelector('.player-name');
            const playerName = playerNameElement ? playerNameElement.textContent : jugadores[j].innerText;
            textoCompartir += (j + 1) + '. ' + playerName + '\n'; // Agrega el jugador con número
        }
        textoCompartir += '\n'; // Agrega una línea en blanco entre equipos
    }
    textoCompartir += 'Generado con: https://armarequipos.com'; // Agrega el enlace al sitio web
    const shareData = {
        title: 'Resultados de los Equipos - Opción ' + (parseInt(indice)),
        text: textoCompartir
    };
    try {
        navigator.share(shareData)
    } catch (err) {
        console.log(`Error: ${err}`);
        // Opción alternativa para navegadores que no soportan Web Share API
        alert('Tu navegador no soporta la función de compartir. Por favor, copia el texto manualmente.');
        navigator.clipboard.writeText(textoCompartir)
          .then(() => {
            alert('Texto copiado al portapapeles');
          })
          .catch(err => {
            console.error('Error al copiar al portapapeles: ', err);
          });
    }
}

// Mostrar u ocultar detalles de los equipos
function toggleStats(button) {
    const contentContainer = button.parentNode.nextElementSibling;
    const textSpan = button.querySelector('span');

    if (contentContainer.style.display === "none" || contentContainer.style.display === "") {
        contentContainer.style.display = "flex";
        textSpan.textContent = "Ocultar detalles";
        createRadarChart(contentContainer);
        createCarousel(contentContainer.querySelector('.carousel-container'));
    } else {
        contentContainer.style.display = "none";
        textSpan.textContent = "Mostrar detalles";
    }
}

function navigateTo(page) {
    const routes = {
        'jugadores': '/jugadores',
        'equipos': '/home',
        'clubes': '/clubes',
        'perfil': '/perfil',
        'partidos': '/partidos'
    };
    
    if (routes[page]) {
        window.location.href = routes[page];
    }
}

// Función común para toggle del sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
}

// Función común para actualizar el icono de contexto
function updateContextIcon() {
    const contextIcon = document.getElementById('contextIcon');
    const selector = document.getElementById('club-select-navbar');
    
    if (selector && selector.value === 'my-players') {
        contextIcon.textContent = '👤'; // Icono de usuario personal
    } else {
        contextIcon.textContent = '⚽'; // Icono de club
    }
}
