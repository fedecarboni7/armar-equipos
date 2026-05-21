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
let closeDetailTimeout = null;
let standingsSort = { key: 'points', direction: 'desc' };
const standingsDateFormatter = new Intl.DateTimeFormat('es-AR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric'
});

function getCurrentVersion() {
    return currentScale === 5 ? 'v1' : 'v2';
}

function getClubIdParam() {
    const clubId = getCurrentClubId();
    return clubId !== 'my-players' ? parseInt(clubId) : null;
}

function formatDateLabel(date) {
    const parsed = new Date(date);
    if (Number.isNaN(parsed.getTime())) {
        return '-';
    }
    const parts = standingsDateFormatter.formatToParts(parsed).reduce((acc, part) => {
        acc[part.type] = part.value;
        return acc;
    }, {});
    const weekday = parts.weekday ? parts.weekday.replace(/\./g, '') : '';
    const month = parts.month ? parts.month.replace(/\./g, '') : '';
    const normalizedWeekday = weekday ? weekday.charAt(0).toUpperCase() + weekday.slice(1) : '';
    const normalizedMonth = month ? month.toLowerCase() : '';
    return `${normalizedWeekday} ${parts.day} ${normalizedMonth} ${parts.year}`.trim();
}

function formatDate(date) {
    return formatDateLabel(date);
}

function formatDateOnly(date) {
    return formatDateLabel(date);
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
        end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59);
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

function getDefaultSortDirection(key) {
    if (key === 'player_name') return 'asc';
    return 'desc';
}

function getStandingsSortValue(row, key) {
    if (key === 'player_name') return row.player_name || '';
    if (key === 'last_match') {
        return row.last_match ? new Date(row.last_match).getTime() : null;
    }
    return row[key] ?? 0;
}

function compareStandings(a, b) {
    const { key, direction } = standingsSort;
    const aValue = getStandingsSortValue(a, key);
    const bValue = getStandingsSortValue(b, key);

    if (aValue == null && bValue == null) return 0;
    if (aValue == null) return 1;
    if (bValue == null) return -1;

    let result = 0;
    if (typeof aValue === 'string') {
        result = aValue.localeCompare(bValue, 'es-AR', { sensitivity: 'base' });
    } else {
        result = aValue - bValue;
    }

    return direction === 'asc' ? result : -result;
}

function getSortedStandings() {
    return [...standings].sort(compareStandings);
}

function updateStandingsSortIndicators() {
    document.querySelectorAll('th.sortable').forEach((header) => {
        const indicator = header.querySelector('.sort-indicator');
        const key = header.dataset.sortKey;
        if (!indicator) return;
        if (key === standingsSort.key) {
            indicator.textContent = standingsSort.direction === 'asc' ? '▲' : '▼';
            header.setAttribute('aria-sort', standingsSort.direction === 'asc' ? 'ascending' : 'descending');
        } else {
            indicator.textContent = '';
            header.setAttribute('aria-sort', 'none');
        }
    });
}

function initStandingsSort() {
    document.querySelectorAll('th.sortable').forEach((header) => {
        header.tabIndex = 0;
        header.setAttribute('role', 'button');

        const onSort = () => {
            const key = header.dataset.sortKey;
            if (!key) return;

            if (standingsSort.key === key) {
                standingsSort.direction = standingsSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                standingsSort = { key, direction: getDefaultSortDirection(key) };
            }

            renderStandings();
        };

        header.addEventListener('click', onSort);
        header.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                onSort();
            }
        });
    });

    updateStandingsSortIndicators();
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

    getSortedStandings().forEach((row) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.player_name}</td>
            <td>${row.points}</td>
            <td>${row.played}</td>
            <td>${row.wins}</td>
            <td>${row.draws}</td>
            <td>${row.losses}</td>
            <td>${row.goals ?? 0}</td>
            <td>${row.assists ?? 0}</td>
            <td>${row.last_match ? formatDateOnly(row.last_match) : '-'}</td>
        `;
        tbody.appendChild(tr);
    });

    updateStandingsSortIndicators();
}

function renderMatches() {
    const list = document.getElementById('matches-list');
    const detail = document.getElementById('match-detail');
    if (detail && list.contains(detail)) {
        list.insertAdjacentElement('afterend', detail);
    }
    list.innerHTML = '';

    document.getElementById('matches-count').textContent = `${matches.length} partidos`;

    closeMatchDetail();

    if (!matches.length) {
        list.innerHTML = '<div class="match-card"><span>No hay partidos para mostrar.</span></div>';
        return;
    }

    matches.forEach((match) => {
        const card = document.createElement('div');
        card.className = 'match-card';
        card.dataset.matchId = match.id;
        const badge = getMatchBadge(match);
        const hasNotes = Boolean(match.notes && match.notes.trim());
        const noteIndicator = hasNotes
            ? '<span class="match-note-indicator" title="Tiene nota"><i class="fa-solid fa-note-sticky"></i></span>'
            : '';

        card.innerHTML = `
            <div class="match-meta">
                <span>${formatDate(match.played_at)} ${noteIndicator}</span>
                <span>${match.players.length} jugadores</span>
            </div>
            <div class="match-score">${match.team_a_score} - ${match.team_b_score}</div>
            <span class="match-badge">${badge}</span>
        `;

        card.addEventListener('click', () => showMatchDetail(match.id, card));
        list.appendChild(card);
    });
}

function closeMatchDetail() {
    const detail = document.getElementById('match-detail');
    if (!detail) return;

    if (closeDetailTimeout) {
        clearTimeout(closeDetailTimeout);
        closeDetailTimeout = null;
    }

    detail.classList.remove('is-open');
    detail.setAttribute('aria-hidden', 'true');

    closeDetailTimeout = window.setTimeout(() => {
        detail.classList.add('hidden');
    }, 260);

    activeMatchId = null;
}

function showMatchDetail(matchId, card) {
    const match = matches.find((item) => item.id === matchId);
    if (!match) return;

    if (activeMatchId === matchId) {
        closeMatchDetail();
        return;
    }

    const detail = document.getElementById('match-detail');
    if (activeMatchId && activeMatchId !== matchId && detail) {
        detail.classList.remove('is-open');
    }

    activeMatchId = matchId;
    if (!card) {
        card = document.querySelector(`.match-card[data-match-id="${matchId}"]`);
    }
    const dateEl = document.getElementById('detail-date');
    const scoreEl = document.getElementById('detail-score');
    const teamAList = document.getElementById('detail-team-a');
    const teamBList = document.getElementById('detail-team-b');
    const noteText = match.notes && match.notes.trim() ? match.notes.trim() : '';

    dateEl.textContent = formatDate(match.played_at);
    scoreEl.textContent = `${match.team_a_score} - ${match.team_b_score}`;
    let notesEl = document.getElementById('detail-notes');
    if (!notesEl && detail) {
        notesEl = document.createElement('p');
        notesEl.id = 'detail-notes';
        detail.insertBefore(notesEl, detail.querySelector('.detail-teams'));
    }
    if (notesEl) {
        if (noteText) {
            notesEl.textContent = noteText;
            notesEl.classList.remove('hidden');
        } else {
            notesEl.textContent = '';
            notesEl.classList.add('hidden');
        }
    }

    teamAList.innerHTML = '';
    teamBList.innerHTML = '';

    const buildPlayerRow = (player) => {
        const li = document.createElement('li');
        const nameSpan = document.createElement('span');
        nameSpan.textContent = getPlayerName(player);
        li.appendChild(nameSpan);

        const goals = player.goals ?? 0;
        const assists = player.assists ?? 0;
        if (goals > 0 || assists > 0) {
            const statsSpan = document.createElement('span');
            statsSpan.className = 'player-stats';
            if (goals > 0 && assists > 0) {
                statsSpan.textContent = `⚽ ${goals}  🅰️ ${assists}`;
            } else if (goals > 0) {
                statsSpan.textContent = `⚽ ${goals}`;
            } else {
                statsSpan.textContent = `🅰️ ${assists}`;
            }
            li.appendChild(statsSpan);
        }
        return li;
    };

    match.players
        .filter((player) => player.team === 'A')
        .forEach((player) => {
            teamAList.appendChild(buildPlayerRow(player));
        });

    match.players
        .filter((player) => player.team === 'B')
        .forEach((player) => {
            teamBList.appendChild(buildPlayerRow(player));
        });

    const canEdit = match.club_id !== null || (currentUser && match.created_by === currentUser.id);
    const editBtn = document.getElementById('edit-match-btn');
    const deleteBtn = document.getElementById('delete-match-btn');

    editBtn.style.display = canEdit ? 'inline-flex' : 'none';
    deleteBtn.style.display = canEdit ? 'inline-flex' : 'none';

    if (card) {
        card.insertAdjacentElement('afterend', detail);
    }

    if (closeDetailTimeout) {
        clearTimeout(closeDetailTimeout);
        closeDetailTimeout = null;
    }
    detail.classList.remove('hidden');
    detail.setAttribute('aria-hidden', 'false');
    requestAnimationFrame(() => {
        detail.classList.add('is-open');
    });
}

function getMatchVersion(match) {
    return match.players.some((player) => player.player_v2_id) ? 10 : 5;
}

async function openMatchModal(mode, match = null) {
    const modal = document.getElementById('match-modal');
    const title = document.getElementById('modal-title');
    const saveBtn = document.getElementById('save-match-btn');
    const dateInput = document.getElementById('match-date');
    const notesInput = document.getElementById('match-notes');
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
    notesInput.value = match && match.notes ? match.notes : '';

    if (modalAssignment) {
        if (match) {
            const teamAEntries = match.players
                .filter((player) => player.team === 'A')
                .map((player) => ({
                    id: player.player_v1_id || player.player_v2_id,
                    goals: player.goals ?? 0,
                    assists: player.assists ?? 0,
                }));
            const teamBEntries = match.players
                .filter((player) => player.team === 'B')
                .map((player) => ({
                    id: player.player_v1_id || player.player_v2_id,
                    goals: player.goals ?? 0,
                    assists: player.assists ?? 0,
                }));
            modalAssignment.setTeams(teamAEntries, teamBEntries);
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
    const notesInput = document.getElementById('match-notes');
    const teamAScore = document.getElementById('team-a-score');
    const teamBScore = document.getElementById('team-b-score');
    const saveBtn = document.getElementById('save-match-btn');

    if (!dateInput.value) {
        showError('Selecciona una fecha para el partido.');
        return;
    }

    if (!modalAssignment) return;
    const teamAEntries = modalAssignment.getTeamEntries('A');
    const teamBEntries = modalAssignment.getTeamEntries('B');
    const teamAIds = teamAEntries.map((entry) => entry.id);
    const teamBIds = teamBEntries.map((entry) => entry.id);

    if (!teamAIds.length && !teamBIds.length) {
        showError('Debes seleccionar jugadores para el partido.');
        return;
    }

    const overlap = teamAIds.filter((id) => teamBIds.includes(id));
    if (overlap.length) {
        showError('Un jugador no puede estar en ambos equipos.');
        return;
    }

    const buildPlayerEntry = (playerEntry, team) => {
        const base = currentScale === 5
            ? { player_v1_id: playerEntry.id, team }
            : { player_v2_id: playerEntry.id, team };
        return {
            ...base,
            goals: playerEntry.goals,
            assists: playerEntry.assists,
        };
    };

    const notesValue = notesInput ? notesInput.value.trim() : '';

    const teamAScoreValue = parseInt(teamAScore.value || 0, 10);
    const teamBScoreValue = parseInt(teamBScore.value || 0, 10);
    const teamAGoals = teamAEntries.reduce((total, entry) => total + (entry.goals || 0), 0);
    const teamBGoals = teamBEntries.reduce((total, entry) => total + (entry.goals || 0), 0);

    if (teamAGoals > teamAScoreValue) {
        showError(`Los goles del Equipo A no pueden superar el marcador (${teamAScoreValue} goles)`);
        return;
    }

    if (teamBGoals > teamBScoreValue) {
        showError(`Los goles del Equipo B no pueden superar el marcador (${teamBScoreValue} goles)`);
        return;
    }

    const teamAAssists = teamAEntries.reduce((total, entry) => total + (entry.assists || 0), 0);
    const teamBAssists = teamBEntries.reduce((total, entry) => total + (entry.assists || 0), 0);

    if (teamAAssists > teamAScoreValue) {
        showError(`Las asistencias del Equipo A no pueden superar el marcador (${teamAScoreValue} goles)`);
        return;
    }

    if (teamBAssists > teamBScoreValue) {
        showError(`Las asistencias del Equipo B no pueden superar el marcador (${teamBScoreValue} goles)`);
        return;
    }

    const payload = {
        played_at: new Date(dateInput.value).toISOString(),
        team_a_score: teamAScoreValue,
        team_b_score: teamBScoreValue,
        notes: notesValue ? notesValue : null,
        players: [
            ...teamAEntries.map((entry) => buildPlayerEntry(entry, 'A')),
            ...teamBEntries.map((entry) => buildPlayerEntry(entry, 'B'))
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
        showError(error.message);
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
        closeMatchDetail();
        await refreshData();
    } catch (error) {
        showError(error.message);
    }
}

async function refreshData() {
    try {
        await Promise.all([loadStandings(), loadMatches()]);
        renderStandings();
        renderMatches();
    } catch (error) {
        showError(error.message);
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
    const rangeSelect = document.getElementById('date-range-select');
    const customRange = document.getElementById('custom-range');

    if (rangeSelect) {
        rangeSelect.value = dateRange;
        if (dateRange === 'custom') {
            customRange.classList.remove('hidden');
        } else {
            customRange.classList.add('hidden');
        }
        rangeSelect.addEventListener('change', () => {
            dateRange = rangeSelect.value;
            if (dateRange === 'custom') {
                customRange.classList.remove('hidden');
            } else {
                customRange.classList.add('hidden');
            }
            refreshData();
        });
    }

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
        enableStatsInputs: true,
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
    initStandingsSort();
    initModalAssignment();

    document.getElementById('new-match-btn').addEventListener('click', () => openMatchModal('create'));
    document.getElementById('close-modal-btn').addEventListener('click', closeMatchModal);
    document.getElementById('cancel-modal-btn').addEventListener('click', closeMatchModal);
    document.getElementById('save-match-btn').addEventListener('click', saveMatch);
    const closeDetailBtn = document.getElementById('close-detail-btn');
    if (closeDetailBtn) {
        closeDetailBtn.addEventListener('click', () => closeMatchDetail());
    }
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
