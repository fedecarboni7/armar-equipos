(function () {
    function create(config) {
        const settings = {
            availableListId: config.availableListId,
            teamAListId: config.teamAListId,
            teamBListId: config.teamBListId,
            teamACountId: config.teamACountId,
            teamBCountId: config.teamBCountId,
            availableCountId: config.availableCountId,
            showRating: Boolean(config.showRating),
            enableSwap: Boolean(config.enableSwap),
            enableStatsInputs: Boolean(config.enableStatsInputs),
            addLabelA: config.addLabelA || 'A',
            addLabelB: config.addLabelB || 'B',
            addButtonClass: config.addButtonClass || 'add-btn',
            addButtonClassB: config.addButtonClassB || 'team-b',
            getEmptyStateHtml: typeof config.getEmptyStateHtml === 'function'
                ? config.getEmptyStateHtml
                : () => config.emptyStateHtml || '',
            getNoResultsHtml: typeof config.getNoResultsHtml === 'function'
                ? config.getNoResultsHtml
                : (term) => (config.noResultsHtml || '').replace('{{search}}', term),
            onChange: typeof config.onChange === 'function' ? config.onChange : null,
        };

        const state = {
            allPlayers: [],
            available: [],
            teamA: [],
            teamB: [],
            searchTerm: '',
            playerStats: new Map(),
        };

        function normalizeTeamEntries(entries) {
            return (entries || []).map((entry) => {
                if (typeof entry === 'number') {
                    return { id: entry, goals: 0, assists: 0 };
                }
                if (entry && typeof entry === 'object') {
                    return {
                        id: entry.id,
                        goals: Number.isFinite(entry.goals) ? entry.goals : 0,
                        assists: Number.isFinite(entry.assists) ? entry.assists : 0,
                    };
                }
                return { id: entry, goals: 0, assists: 0 };
            });
        }

        function getPlayerStats(playerId) {
            if (!settings.enableStatsInputs) {
                return { goals: 0, assists: 0 };
            }
            return state.playerStats.get(playerId) || { goals: 0, assists: 0 };
        }

        function sortPlayersByName(list) {
            return [...list].sort((a, b) => a.name.localeCompare(b.name, 'es', { sensitivity: 'base' }));
        }

        function escapeText(value) {
            return String(value)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }

        function getContainer(id) {
            return id ? document.getElementById(id) : null;
        }

        function setPlayers(players) {
            state.allPlayers = players ? [...players] : [];
            state.available = sortPlayersByName(state.allPlayers);
            state.teamA = [];
            state.teamB = [];
            state.playerStats = new Map();
            render();
        }

        function setTeams(teamAIds, teamBIds) {
            const map = new Map(state.allPlayers.map((player) => [player.id, player]));
            const teamAEntries = normalizeTeamEntries(teamAIds);
            const teamBEntries = normalizeTeamEntries(teamBIds);
            state.playerStats = new Map();
            state.teamA = teamAEntries
                .map((entry) => {
                    const player = map.get(entry.id);
                    if (player && settings.enableStatsInputs) {
                        state.playerStats.set(entry.id, { goals: entry.goals, assists: entry.assists });
                    }
                    return player;
                })
                .filter(Boolean);
            state.teamB = teamBEntries
                .map((entry) => {
                    const player = map.get(entry.id);
                    if (player && settings.enableStatsInputs) {
                        state.playerStats.set(entry.id, { goals: entry.goals, assists: entry.assists });
                    }
                    return player;
                })
                .filter(Boolean);
            const selectedIds = new Set([
                ...teamAEntries.map((entry) => entry.id),
                ...teamBEntries.map((entry) => entry.id),
            ]);
            state.available = sortPlayersByName(
                state.allPlayers.filter((player) => !selectedIds.has(player.id))
            );
            render();
        }

        function setSearchTerm(term) {
            state.searchTerm = String(term || '').toLowerCase().trim();
            renderAvailable();
        }

        function renderAvailable() {
            const container = getContainer(settings.availableListId);
            if (!container) return;

            container.innerHTML = '';
            const playersToShow = state.available.filter((player) =>
                player.name.toLowerCase().includes(state.searchTerm)
            );

            const emptyStateHtml = settings.getEmptyStateHtml();
            if (!state.available.length && emptyStateHtml) {
                container.innerHTML = emptyStateHtml;
                return;
            }

            if (!playersToShow.length) {
                const term = escapeText(state.searchTerm);
                const noResultsHtml = settings.getNoResultsHtml(term);
                if (noResultsHtml) {
                    container.innerHTML = noResultsHtml;
                }
                return;
            }

            playersToShow.forEach((player) => {
                const row = document.createElement('div');
                row.className = 'available-player';
                row.innerHTML = `
                    <div class="player-info">
                        <span class="player-name">${player.name}</span>
                        ${settings.showRating && player.rating !== undefined ? `<span class="player-rating">${player.rating}</span>` : ''}
                    </div>
                    <div class="add-buttons">
                        <button class="${settings.addButtonClass}" data-team="A" data-player="${player.id}">${settings.addLabelA}</button>
                        <button class="${settings.addButtonClass} ${settings.addButtonClassB}" data-team="B" data-player="${player.id}">${settings.addLabelB}</button>
                    </div>
                `;
                row.querySelectorAll('button').forEach((button) => {
                    button.addEventListener('click', () => {
                        addToTeam(button.dataset.team, parseInt(button.dataset.player, 10));
                    });
                });
                container.appendChild(row);
            });
        }

        function renderTeam(teamName, team, containerId) {
            const container = getContainer(containerId);
            if (!container) return;

            container.innerHTML = '';
            team.forEach((player) => {
                const stats = getPlayerStats(player.id);
                const row = document.createElement('div');
                row.className = 'team-player';
                const swapButton = settings.enableSwap
                    ? `<button class="swap-btn" data-team="${teamName}" data-player="${player.id}"><i class="fa-solid fa-right-left"></i></button>`
                    : '';
                const statsInputs = settings.enableStatsInputs
                    ? `
                        <div class="team-stats">
                            <label class="team-stat">
                                <span>G</span>
                                <input type="number" min="0" max="99" value="${stats.goals}" data-stat="goals" data-player="${player.id}" aria-label="Goles" />
                            </label>
                            <label class="team-stat">
                                <span>A</span>
                                <input type="number" min="0" max="99" value="${stats.assists}" data-stat="assists" data-player="${player.id}" aria-label="Asistencias" />
                            </label>
                        </div>
                    `
                    : '';
                row.innerHTML = `
                    <div class="player-info">
                        <span class="player-name">${player.name}</span>
                        ${settings.showRating && player.rating !== undefined ? `<span class="player-rating">${player.rating}</span>` : ''}
                    </div>
                    <div class="team-actions">
                        ${statsInputs}
                        ${swapButton}
                        <button class="remove-btn" data-team="${teamName}" data-player="${player.id}"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                `;
                if (settings.enableStatsInputs) {
                    row.querySelectorAll('input[data-stat]').forEach((input) => {
                        input.addEventListener('input', () => {
                            const playerId = parseInt(input.dataset.player, 10);
                            const stat = input.dataset.stat;
                            const current = state.playerStats.get(playerId) || { goals: 0, assists: 0 };
                            const parsed = parseInt(input.value || '0', 10);
                            const value = Number.isNaN(parsed) ? 0 : Math.max(0, parsed);
                            state.playerStats.set(playerId, {
                                goals: stat === 'goals' ? value : current.goals,
                                assists: stat === 'assists' ? value : current.assists,
                            });
                        });
                    });
                }
                row.querySelectorAll('button').forEach((button) => {
                    button.addEventListener('click', () => {
                        const team = button.dataset.team;
                        const playerId = parseInt(button.dataset.player, 10);
                        if (button.classList.contains('swap-btn')) {
                            swapTeam(team, playerId);
                        } else {
                            removeFromTeam(team, playerId);
                        }
                    });
                });
                container.appendChild(row);
            });
        }

        function updateCounts() {
            const teamACount = getContainer(settings.teamACountId);
            const teamBCount = getContainer(settings.teamBCountId);
            const availableCount = getContainer(settings.availableCountId);

            if (teamACount) teamACount.textContent = `${state.teamA.length} jugadores`;
            if (teamBCount) teamBCount.textContent = `${state.teamB.length} jugadores`;
            if (availableCount) availableCount.textContent = `${state.available.length} jugadores`;
        }

        function render() {
            renderAvailable();
            renderTeam('A', state.teamA, settings.teamAListId);
            renderTeam('B', state.teamB, settings.teamBListId);
            updateCounts();
            if (settings.onChange) {
                settings.onChange({
                    teamA: [...state.teamA],
                    teamB: [...state.teamB],
                    available: [...state.available],
                });
            }
        }

        function addToTeam(teamName, playerId) {
            const player = state.available.find((item) => item.id === playerId);
            if (!player) return;

            if (teamName === 'A') {
                state.teamA.push(player);
            } else {
                state.teamB.push(player);
            }

            if (settings.enableStatsInputs && !state.playerStats.has(playerId)) {
                state.playerStats.set(playerId, { goals: 0, assists: 0 });
            }

            state.available = sortPlayersByName(state.available.filter((item) => item.id !== playerId));
            render();
        }

        function removeFromTeam(teamName, playerId) {
            let player;
            if (teamName === 'A') {
                player = state.teamA.find((item) => item.id === playerId);
                state.teamA = state.teamA.filter((item) => item.id !== playerId);
            } else {
                player = state.teamB.find((item) => item.id === playerId);
                state.teamB = state.teamB.filter((item) => item.id !== playerId);
            }

            if (player) {
                state.available = sortPlayersByName([...state.available, player]);
            }
            if (settings.enableStatsInputs) {
                state.playerStats.delete(playerId);
            }
            render();
        }

        function swapTeam(currentTeam, playerId) {
            let player;
            if (currentTeam === 'A') {
                player = state.teamA.find((item) => item.id === playerId);
                state.teamA = state.teamA.filter((item) => item.id !== playerId);
                if (player) state.teamB.push(player);
            } else {
                player = state.teamB.find((item) => item.id === playerId);
                state.teamB = state.teamB.filter((item) => item.id !== playerId);
                if (player) state.teamA.push(player);
            }
            render();
        }

        function reset() {
            state.available = sortPlayersByName(state.allPlayers);
            state.teamA = [];
            state.teamB = [];
            state.playerStats = new Map();
            render();
        }

        function getTeamA() {
            return [...state.teamA];
        }

        function getTeamB() {
            return [...state.teamB];
        }

        function getTeamIds(teamName) {
            const list = teamName === 'A' ? state.teamA : state.teamB;
            return list.map((player) => player.id);
        }

        function getTeamEntries(teamName) {
            const list = teamName === 'A' ? state.teamA : state.teamB;
            return list.map((player) => {
                const stats = getPlayerStats(player.id);
                return { id: player.id, goals: stats.goals, assists: stats.assists };
            });
        }

        return {
            setPlayers,
            setTeams,
            setSearchTerm,
            render,
            reset,
            getTeamA,
            getTeamB,
            getTeamIds,
            getTeamEntries,
        };
    }

    window.TeamAssignment = { create };
})();
