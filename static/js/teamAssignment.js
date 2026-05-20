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
        };

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
            render();
        }

        function setTeams(teamAIds, teamBIds) {
            const map = new Map(state.allPlayers.map((player) => [player.id, player]));
            state.teamA = teamAIds.map((id) => map.get(id)).filter(Boolean);
            state.teamB = teamBIds.map((id) => map.get(id)).filter(Boolean);
            const selectedIds = new Set([...teamAIds, ...teamBIds]);
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
                        <span class="player-name">👤 ${player.name}</span>
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
                const row = document.createElement('div');
                row.className = 'team-player';
                const swapButton = settings.enableSwap
                    ? `<button class="swap-btn" data-team="${teamName}" data-player="${player.id}"><i class="fa-solid fa-right-left"></i></button>`
                    : '';
                row.innerHTML = `
                    <div class="player-info">
                        <span class="player-name">👤 ${player.name}</span>
                        ${settings.showRating && player.rating !== undefined ? `<span class="player-rating">${player.rating}</span>` : ''}
                    </div>
                    <div class="team-actions">
                        ${swapButton}
                        <button class="remove-btn" data-team="${teamName}" data-player="${player.id}"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                `;
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

        return {
            setPlayers,
            setTeams,
            setSearchTerm,
            render,
            reset,
            getTeamA,
            getTeamB,
            getTeamIds,
        };
    }

    window.TeamAssignment = { create };
})();
