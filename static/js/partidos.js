let currentScale = 5;
let matches = [];
let standings = [];
let playersV1 = [];
let playersV2 = [];
let playerMapV1 = new Map();
let playerMapV2 = new Map();
let currentUser = null;
let activeMatchId = null;
let isEditMode = false;
let dateRange = 'month';
let pendingEditMatch = null;
let modalAssignment = null;

function getCurrentVersion() {
    return currentScale === 5 ? 'v1' : 'v2';
}

function getClubIdParam() {
    const clubId = getCurrentClubId();
    return clubId !== 'my-players' ? parseInt(clubId) : null;
}

function formatDate(date) {
    const parsed = new Date(date);
    if (Number.isNaN(parsed.getTime())) {
        return '-';
    }
    return parsed.toLocaleDateString('es-ES') + ' ' + parsed.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

function formatDateOnly(date) {
    const parsed = new Date(date);
    if (Number.isNaN(parsed.getTime())) {
        return '-';
    }
    return parsed.toLocaleDateString('es-ES');
}

function toDatetimeLocalValue(date) {
    const parsed = new Date(date);
    if (Number.isNaN(parsed.getTime())) {
        return '';
    }
    const offset = parsed.getTimezoneOffset() * 60000;
    const local = new Date(parsed.getTime() - offset);
    return local.toISOString().slice(0, 16);
}

function showErrorMessage(message) {
    if (typeof showError === 'function') {
        showError(message);
        return;
    }
    alert(message);
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        ...options
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Error del servidor' }));
        throw new Error(errorData.detail || 'Error del servidor');
    }
    return response.json();
}

function getDateRangeParams() {
    const now = new Date();
    let start = null;
    let end = null;

    if (dateRange === 'month') {
        start = new Date(now.getFullYear(), now.getMonth(), 1);
        end = now;
    } else if (dateRange === 'quarter') {
        start = new Date(now);
        start.setMonth(start.getMonth() - 3);
        end = now;
    } else if (dateRange === 'year') {
        start = new Date(now);
        start.setFullYear(start.getFullYear() - 1);
        end = now;
    } else if (dateRange === 'custom') {
        const fromInput = document.getElementById('date-from');
        const toInput = document.getElementById('date-to');
        if (fromInput && fromInput.value) {
            start = new Date(`${fromInput.value}T00:00:00`);
        }
        if (toInput && toInput.value) {
            end = new Date(`${toInput.value}T23:59:59`);
        }
    }

    const params = {};
    if (start) {
        params.start_date = start.toISOString();
    }
    if (end) {
        params.end_date = end.toISOString();
    }
    return params;
}

async function loadPlayersForContext() {
    const clubId = getClubIdParam();
    const [v1Players, v2Players] = await Promise.all([
        TeamsAPI.getPlayers(clubId, '1-5'),
        TeamsAPI.getPlayers(clubId, '1-10')
    ]);
    playersV1 = v1Players || [];
    playersV2 = v2Players || [];
    playerMapV1 = new Map(playersV1.map((player) => [player.id, player.name]));
    playerMapV2 = new Map(playersV2.map((player) => [player.id, player.name]));
    if (modalAssignment) {
        modalAssignment.setPlayers(currentScale === 5 ? playersV1 : playersV2);
    }
}

async function loadMatches() {
    const params = new URLSearchParams();
    const clubId = getClubIdParam();
    if (clubId) {
        params.set('club_id', clubId);
    }
    const rangeParams = getDateRangeParams();
    if (rangeParams.start_date) params.set('start_date', rangeParams.start_date);
    if (rangeParams.end_date) params.set('end_date', rangeParams.end_date);

    const url = params.toString() ? `/matches?${params.toString()}` : '/matches';
    matches = await fetchJson(url);
}

async function loadStandings() {
    const params = new URLSearchParams();
    params.set('version', getCurrentVersion());
    const clubId = getClubIdParam();
    if (clubId) {
        params.set('club_id', clubId);
    }
    const rangeParams = getDateRangeParams();
    if (rangeParams.start_date) params.set('start_date', rangeParams.start_date);
    if (rangeParams.end_date) params.set('end_date', rangeParams.end_date);

    standings = await fetchJson(`/matches/standings?${params.toString()}`);
}

function getPlayerName(matchPlayer) {
    if (matchPlayer.player_v1_id) {
        return playerMapV1.get(matchPlayer.player_v1_id) || `Jugador ${matchPlayer.player_v1_id}`;
    }
    if (matchPlayer.player_v2_id) {
        return playerMapV2.get(matchPlayer.player_v2_id) || `Jugador ${matchPlayer.player_v2_id}`;
    }
    return 'Jugador';
}

function getMatchBadge(match) {
    if (match.team_a_score === match.team_b_score) {
        return 'Empate';
    }
    return match.team_a_score > match.team_b_score ? 'Ganó A' : 'Ganó B';
}

function renderStandings() {
    const tbody = document.getElementById('standings-body');
    const empty = document.getElementById('standings-empty');
    const count = document.getElementById('standings-count');
    tbody.innerHTML = '';

    if (!standings.length) {
        empty.classList.remove('hidden');
        count.textContent = '0 jugadores';
        return;
    }

    empty.classList.add('hidden');
    count.textContent = `${standings.length} jugadores`;

    standings.forEach((row) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.player_name}</td>
            <td>${row.points}</td>
            <td>${row.played}</td>
            <td>${row.wins}</td>
            <td>${row.draws}</td>
            <td>${row.losses}</td>
            <td>${row.last_match ? formatDateOnly(row.last_match) : '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderMatches() {
    const list = document.getElementById('matches-list');
    list.innerHTML = '';

    document.getElementById('matches-count').textContent = `${matches.length} partidos`;

    if (!matches.length) {
        list.innerHTML = '<div class="match-card"><span>No hay partidos para mostrar.</span></div>';
        return;
    }

    matches.forEach((match) => {
        const card = document.createElement('div');
        card.className = 'match-card';
        const badge = getMatchBadge(match);

        card.innerHTML = `
            <div class="match-meta">
                <span>${formatDate(match.played_at)}</span>
                <span>${match.players.length} jugadores</span>
            </div>
            <div class="match-score">${match.team_a_score} - ${match.team_b_score}</div>
            <span class="match-badge">${badge}</span>
        `;

        card.addEventListener('click', () => showMatchDetail(match.id));
        list.appendChild(card);
    });
}

function showMatchDetail(matchId) {
    const match = matches.find((item) => item.id === matchId);
    if (!match) return;

    activeMatchId = matchId;
    const detail = document.getElementById('match-detail');
    const dateEl = document.getElementById('detail-date');
    const scoreEl = document.getElementById('detail-score');
    const teamAList = document.getElementById('detail-team-a');
    const teamBList = document.getElementById('detail-team-b');

    dateEl.textContent = formatDate(match.played_at);
    scoreEl.textContent = `${match.team_a_score} - ${match.team_b_score}`;

    teamAList.innerHTML = '';
    teamBList.innerHTML = '';

    match.players
        .filter((player) => player.team === 'A')
        .forEach((player) => {
            const li = document.createElement('li');
            li.textContent = getPlayerName(player);
            teamAList.appendChild(li);
        });

    match.players
        .filter((player) => player.team === 'B')
        .forEach((player) => {
            const li = document.createElement('li');
            li.textContent = getPlayerName(player);
            teamBList.appendChild(li);
        });

    const canEdit = match.club_id !== null || (currentUser && match.created_by === currentUser.id);
    const editBtn = document.getElementById('edit-match-btn');
    const deleteBtn = document.getElementById('delete-match-btn');

    editBtn.style.display = canEdit ? 'inline-flex' : 'none';
    deleteBtn.style.display = canEdit ? 'inline-flex' : 'none';

    detail.classList.remove('hidden');
}

function getMatchVersion(match) {
    return match.players.some((player) => player.player_v2_id) ? 10 : 5;
}

async function openMatchModal(mode, match = null) {
    const modal = document.getElementById('match-modal');
    const title = document.getElementById('modal-title');
    const saveBtn = document.getElementById('save-match-btn');
    const dateInput = document.getElementById('match-date');
    const teamAScore = document.getElementById('team-a-score');
    const teamBScore = document.getElementById('team-b-score');

    isEditMode = mode === 'edit';

    if (match && currentScale !== getMatchVersion(match)) {
        pendingEditMatch = match;
        setScale(getMatchVersion(match));
        return;
    }

    modal.classList.add('active');
    title.textContent = isEditMode ? 'Editar partido' : 'Nuevo partido';
    saveBtn.textContent = isEditMode ? 'Guardar cambios' : 'Guardar';

    dateInput.value = match ? toDatetimeLocalValue(match.played_at) : '';
    teamAScore.value = match ? match.team_a_score : 0;
    teamBScore.value = match ? match.team_b_score : 0;

    if (modalAssignment) {
        if (match) {
            const teamAIds = match.players.filter((player) => player.team === 'A').map((player) => player.player_v1_id || player.player_v2_id);
            const teamBIds = match.players.filter((player) => player.team === 'B').map((player) => player.player_v1_id || player.player_v2_id);
            modalAssignment.setTeams(teamAIds, teamBIds);
        } else {
            modalAssignment.reset();
        }
    }
}

function closeMatchModal() {
    document.getElementById('match-modal').classList.remove('active');
}

async function saveMatch() {
    const dateInput = document.getElementById('match-date');
    const teamAScore = document.getElementById('team-a-score');
    const teamBScore = document.getElementById('team-b-score');
    const saveBtn = document.getElementById('save-match-btn');

    if (!dateInput.value) {
        showErrorMessage('Selecciona una fecha para el partido.');
        return;
    }

    if (!modalAssignment) return;
    const teamAIds = modalAssignment.getTeamIds('A');
    const teamBIds = modalAssignment.getTeamIds('B');

    if (!teamAIds.length && !teamBIds.length) {
        showErrorMessage('Debes seleccionar jugadores para el partido.');
        return;
    }

    const overlap = teamAIds.filter((id) => teamBIds.includes(id));
    if (overlap.length) {
        showErrorMessage('Un jugador no puede estar en ambos equipos.');
        return;
    }

    const buildPlayerEntry = (playerId, team) => {
        return currentScale === 5
            ? { player_v1_id: playerId, team }
            : { player_v2_id: playerId, team };
    };

    const payload = {
        played_at: new Date(dateInput.value).toISOString(),
        team_a_score: parseInt(teamAScore.value || 0, 10),
        team_b_score: parseInt(teamBScore.value || 0, 10),
        players: [
            ...teamAIds.map((id) => buildPlayerEntry(id, 'A')),
            ...teamBIds.map((id) => buildPlayerEntry(id, 'B'))
        ]
    };

    if (!isEditMode) {
        const clubId = getClubIdParam();
        if (clubId) {
            payload.club_id = clubId;
        }
    }

    saveBtn.disabled = true;
    saveBtn.textContent = 'Guardando...';

    try {
        if (isEditMode && activeMatchId) {
            await fetchJson(`/matches/${activeMatchId}`, {
                method: 'PATCH',
                body: JSON.stringify(payload)
            });
        } else {
            await fetchJson('/matches', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
        }
        closeMatchModal();
        await refreshData();
        if (activeMatchId) {
            showMatchDetail(activeMatchId);
        }
    } catch (error) {
        showErrorMessage(error.message);
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = isEditMode ? 'Guardar cambios' : 'Guardar';
    }
}

async function deleteMatch() {
    if (!activeMatchId) return;
    if (!confirm('Eliminar este partido?')) return;

    try {
        await fetchJson(`/matches/${activeMatchId}`, { method: 'DELETE' });
        activeMatchId = null;
        document.getElementById('match-detail').classList.add('hidden');
        await refreshData();
    } catch (error) {
        showErrorMessage(error.message);
    }
}

async function refreshData() {
    try {
        await Promise.all([loadStandings(), loadMatches()]);
        renderStandings();
        renderMatches();
    } catch (error) {
        showErrorMessage(error.message);
    }
}

async function setScale(scale) {
    currentScale = scale;

    document.querySelectorAll('.scale-option').forEach((button) => {
        button.classList.remove('active');
    });

    if (typeof event !== 'undefined' && event.target) {
        event.target.classList.add('active');
    } else {
        const index = currentScale === 5 ? 0 : 1;
        const buttons = document.querySelectorAll('.scale-option');
        if (buttons[index]) {
            buttons[index].classList.add('active');
        }
    }

    if (modalAssignment) {
        modalAssignment.setPlayers(currentScale === 5 ? playersV1 : playersV2);
    }

    await refreshData();

    if (pendingEditMatch) {
        const matchToEdit = pendingEditMatch;
        pendingEditMatch = null;
        openMatchModal('edit', matchToEdit);
    }
}

function initDateFilters() {
    document.querySelectorAll('.date-option').forEach((button) => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.date-option').forEach((btn) => btn.classList.remove('active'));
            button.classList.add('active');
            dateRange = button.dataset.range;
            const customRange = document.getElementById('custom-range');
            if (dateRange === 'custom') {
                customRange.classList.remove('hidden');
            } else {
                customRange.classList.add('hidden');
            }
            refreshData();
        });
    });

    const fromInput = document.getElementById('date-from');
    const toInput = document.getElementById('date-to');
    if (fromInput) {
        fromInput.addEventListener('change', refreshData);
    }
    if (toInput) {
        toInput.addEventListener('change', refreshData);
    }
}

function initModalAssignment() {
    if (!window.TeamAssignment) return;
    modalAssignment = window.TeamAssignment.create({
        availableListId: 'modal-available-players',
        teamAListId: 'modal-team-a',
        teamBListId: 'modal-team-b',
        teamACountId: 'modal-team-a-count',
        teamBCountId: 'modal-team-b-count',
        availableCountId: 'modal-available-count',
        showRating: false,
        enableSwap: false,
        addLabelA: '➜ A',
        addLabelB: '➜ B',
        addButtonClass: 'add-btn',
        addButtonClassB: 'team-b',
        getEmptyStateHtml: () => '<div class="standings-empty">No hay jugadores disponibles.</div>',
        getNoResultsHtml: (term) => `<div class="standings-empty">No se encontraron jugadores con "${term}".</div>`,
    });

    const searchInput = document.getElementById('modal-player-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            if (modalAssignment) {
                modalAssignment.setSearchTerm(e.target.value);
            }
        });
    }
}

async function initPartidos() {
    const userData = document.getElementById('user-data');
    if (userData) {
        try {
            currentUser = JSON.parse(userData.textContent);
        } catch (error) {
            currentUser = null;
        }
    }

    initDateFilters();
    initModalAssignment();

    document.getElementById('new-match-btn').addEventListener('click', () => openMatchModal('create'));
    document.getElementById('close-modal-btn').addEventListener('click', closeMatchModal);
    document.getElementById('cancel-modal-btn').addEventListener('click', closeMatchModal);
    document.getElementById('save-match-btn').addEventListener('click', saveMatch);
    document.getElementById('edit-match-btn').addEventListener('click', () => {
        const match = matches.find((item) => item.id === activeMatchId);
        if (match) {
            openMatchModal('edit', match);
        }
    });
    document.getElementById('delete-match-btn').addEventListener('click', deleteMatch);

    await loadPlayersForContext();
    await refreshData();
}

window.onContextChanged = async function () {
    await loadPlayersForContext();
    await refreshData();
};

document.addEventListener('DOMContentLoaded', initPartidos);
