const publicSkillLabels = [
    ['velocidad', 'Velocidad'],
    ['fuerza_cuerpo', 'Cuerpo'],
    ['pases', 'Pases'],
    ['habilidad_arquero', 'Arquero'],
    ['defensa', 'Defensa'],
    ['resistencia', 'Resistencia'],
    ['control', 'Control'],
    ['tiro', 'Tiro'],
    ['vision', 'Visión']
];

function renderPublicPlayer(player) {
    const content = document.getElementById('public-player-content');
    const scale = player.scale === 's10' ? 10 : 5;
    content.innerHTML = `
        <div class="public-player-heading">
            <div class="public-player-avatar">
                ${renderPlayerAvatar(player, 112)}
            </div>
            <div>
                <p class="public-kicker">Perfil público</p>
                <h1>${escapeHTML(player.name)}</h1>
                <p class="public-scale">Escala 1-${scale}</p>
            </div>
        </div>
        <div class="public-chart-container">
            <canvas id="public-player-chart" width="420" height="420"></canvas>
        </div>
    `;

    createRadarChart('public-player-chart', player, scale, 'public');
}

function renderPublicPlayerMessage(message, className) {
    document.getElementById('public-player-content').innerHTML =
        `<div class="public-player-message ${className}">${message}</div>`;
}

async function loadPublicPlayer() {
    const token = document.body.dataset.token;
    try {
        const response = await fetch(`/public/players/${encodeURIComponent(token)}`);
        if (response.status === 404) {
            renderPublicPlayerMessage('Este link no está disponible o fue revocado.', 'is-error');
            return;
        }
        if (response.status === 429) {
            renderPublicPlayerMessage('Hay muchas visitas en este momento. Intentá de nuevo en un rato.', 'is-error');
            return;
        }
        if (!response.ok) {
            throw new Error(`Error ${response.status}`);
        }
        renderPublicPlayer(await response.json());
    } catch (error) {
        console.error('Error loading public player:', error);
        renderPublicPlayerMessage('No pudimos cargar este perfil. Intentá de nuevo más tarde.', 'is-error');
    }
}

document.addEventListener('DOMContentLoaded', loadPublicPlayer);
