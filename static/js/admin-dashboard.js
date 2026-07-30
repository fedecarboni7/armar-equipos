function createIcon(name, className = '') {
    const iconMap = {
        users: `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="m22 21-3.5-3.5"/></svg>`,
        'user-check': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16,11 18,13 22,9"/></svg>`,
        trophy: `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55.47.98.97 1.21C12.04 18.75 13 20.24 13 22"/><path d="M14 14.66V17c0 .55-.47.98-.97 1.21C11.96 18.75 11 20.24 11 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/></svg>`,
        zap: `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><polygon points="13,2 3,14 12,14 11,22 21,10 12,10 13,2"/></svg>`,
        clock: `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>`,
        'trending-up': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><polyline points="22,7 13.5,15.5 8.5,10.5 2,17"/><polyline points="16,7 22,7 22,13"/></svg>`,
        'map-pin': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>`,
        mail: `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>`,
        alert: `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3.05h16.94a2 2 0 0 0 1.71-3.05L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    };

    return iconMap[name] || '';
}

let dashboardStats = null;
let fullDailyNewUsers = [];
let fullDailyNewClubs = [];

function initializeDashboard(stats) {
    dashboardStats = stats;
    fullDailyNewUsers = stats.daily_new_users || [];
    fullDailyNewClubs = stats.daily_new_clubs || [];
}

function getPeriodData(type, period) {
    const dataMap = {
        active: {
            '24h': { value: dashboardStats.active_users_24h, label: 'Últimas 24 horas', color: '#fb923c' },
            '7d': { value: dashboardStats.active_users_7d, label: 'Últimos 7 días', color: '#818cf8' },
            '30d': { value: dashboardStats.active_users_30d, label: 'Últimos 30 días', color: '#f472b6' },
        },
    };

    return dataMap[type]?.[period];
}

function updatePeriodCard(type, period, valueId, subtitleId, buttonClass) {
    const data = getPeriodData(type, period);
    if (!data) {
        return;
    }

    const valueElement = document.getElementById(valueId);
    const subtitleElement = document.getElementById(subtitleId);

    if (valueElement) {
        valueElement.textContent = data.value;
    }

    if (subtitleElement) {
        subtitleElement.textContent = data.label;
        subtitleElement.style.color = data.color;
    }

    document.querySelectorAll(`.${buttonClass}`).forEach((button) => {
        button.classList.remove('active');
    });

    const activeButton = document.querySelector(`.${buttonClass}[data-period="${period}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
}

function changeActiveUsersPeriod(period) {
    updatePeriodCard('active', period, 'active-users-value', 'active-users-subtitle', 'period-btn-active');
}

function changeUsersChartRange(days, btn) {
    const container = document.getElementById('users-chart-content');
    const sliced = fullDailyNewUsers.slice(-days);
    const total = sliced.reduce((sum, d) => sum + (Number(d.count) || 0), 0);

    const totalEl = document.getElementById('users-chart-total');
    if (totalEl) {
        const label = days <= 1 ? 'hoy' : ``;
        totalEl.textContent = `${total} usuario${total !== 1 ? 's' : ''} nuevo${total !== 1 ? 's' : ''} ${label}`;
    }

    if (days === 1) {
        const last = sliced[sliced.length - 1];
        const value = last ? Number(last.count) || 0 : 0;
        container.innerHTML = `<div class="chart-single-value"><p class="metric-value">${value}</p><p class="metric-subtitle">Usuarios nuevos hoy</p></div>`;
    } else {
        container.innerHTML = createLineChart(sliced, '#fb923c', 'usuarios nuevos');
    }
    document.querySelectorAll('.period-btn-users-chart').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
}

function changeClubsChartRange(days, btn) {
    const container = document.getElementById('clubs-chart-content');
    const sliced = fullDailyNewClubs.slice(-days);
    const total = sliced.reduce((sum, d) => sum + (Number(d.count) || 0), 0);

    const totalEl = document.getElementById('clubs-chart-total');
    if (totalEl) {
        const label = days <= 1 ? 'hoy' : ``;
        totalEl.textContent = `${total} club${total !== 1 ? 'es' : ''} nuevo${total !== 1 ? 's' : ''} ${label}`;
    }

    if (days === 1) {
        const last = sliced[sliced.length - 1];
        const value = last ? Number(last.count) || 0 : 0;
        container.innerHTML = `<div class="chart-single-value"><p class="metric-value">${value}</p><p class="metric-subtitle">Clubes nuevos hoy</p></div>`;
    } else {
        container.innerHTML = createLineChart(sliced, '#818cf8', 'clubes nuevos');
    }
    document.querySelectorAll('.period-btn-clubs-chart').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
}

function formatShortDate(dateString) {
    return dateString.slice(5);
}

let chartTooltip = null;

function showChartTooltip(event, text) {
    if (!chartTooltip) {
        chartTooltip = document.createElement('div');
        chartTooltip.className = 'chart-tooltip';
        document.body.appendChild(chartTooltip);
    }
    chartTooltip.textContent = text;
    chartTooltip.style.display = 'block';
    const rect = chartTooltip.getBoundingClientRect();
    let left = event.clientX - rect.width / 2;
    let top = event.clientY - rect.height - 12;
    if (left < 4) left = 4;
    if (left + rect.width > window.innerWidth - 4) left = window.innerWidth - rect.width - 4;
    if (top < 4) top = event.clientY + 16;
    chartTooltip.style.left = left + 'px';
    chartTooltip.style.top = top + 'px';
}

function hideChartTooltip() {
    if (chartTooltip) chartTooltip.style.display = 'none';
}

function createLineChart(data, color, tooltipLabel = '') {
    if (!Array.isArray(data) || data.length === 0) {
        return '<div class="chart-empty">Sin datos disponibles</div>';
    }

    const width = 760;
    const height = 220;
    const paddingX = 50;
    const paddingTop = 16;
    const paddingBottom = 30;
    const chartWidth = width - paddingX * 2;
    const chartHeight = height - paddingTop - paddingBottom;

    const maxValue = Math.max(1, ...data.map((item) => Number(item.count) || 0));
    const stepX = data.length > 1 ? chartWidth / (data.length - 1) : 0;

    const tickCount = 5;
    const gridlines = [];
    for (let i = 0; i <= tickCount; i++) {
        const tickValue = Math.round((maxValue * i) / tickCount);
        const y = paddingTop + chartHeight - (tickValue / maxValue) * chartHeight;
        gridlines.push(`<line x1="${paddingX}" y1="${y}" x2="${width - paddingX}" y2="${y}" class="chart-gridline" />`);
        gridlines.push(`<text x="${paddingX - 6}" y="${y + 3.5}" class="chart-tick-label" text-anchor="end">${tickValue}</text>`);
    }

    const points = data.map((item, index) => {
        const value = Number(item.count) || 0;
        const x = paddingX + index * stepX;
        const y = paddingTop + chartHeight - (value / maxValue) * chartHeight;
        return `${x},${y}`;
    });

    const labels = [0, Math.floor(data.length / 2), data.length - 1]
        .filter((index, pos, arr) => arr.indexOf(index) === pos)
        .map((index) => {
            const x = paddingX + index * stepX;
            const label = formatShortDate(data[index].date);
            return `<text x="${x}" y="${height - 8}" class="chart-axis-label" text-anchor="middle">${label}</text>`;
        })
        .join('');

    return `
        <svg class="svg-chart" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="Gráfico de línea">
            ${gridlines.join('')}
            <line x1="${paddingX}" y1="${paddingTop + chartHeight}" x2="${width - paddingX}" y2="${paddingTop + chartHeight}" class="chart-axis" />
            <polyline points="${points.join(' ')}" fill="none" stroke="${color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
            ${data
                .map((item, index) => {
                    const value = Number(item.count) || 0;
                    const x = paddingX + index * stepX;
                    const y = paddingTop + chartHeight - (value / maxValue) * chartHeight;
                    if (value === 0) return '';
                    const labelText = `${formatShortDate(item.date)}: ${value} ${tooltipLabel}`;
                    return `<circle cx="${x}" cy="${y}" r="12" fill="transparent" style="cursor:pointer" onmouseenter="showChartTooltip(event,'${labelText}')" onmouseleave="hideChartTooltip()" /><circle cx="${x}" cy="${y}" r="4" fill="${color}" pointer-events="none" />`;
                })
                .join('')}
            ${labels}
        </svg>
    `;
}

function createStackedBarChart(data) {
    if (!Array.isArray(data) || data.length === 0) {
        return '<div class="chart-empty">Sin datos disponibles</div>';
    }

    const width = 1100;
    const height = 220;
    const paddingX = 50;
    const paddingTop = 16;
    const paddingBottom = 34;
    const chartWidth = width - paddingX * 2;
    const chartHeight = height - paddingTop - paddingBottom;
    const barWidth = chartWidth / Math.max(data.length, 1) - 8;

    const totals = data.map((item) => (Number(item.club_matches) || 0) + (Number(item.individual_matches) || 0));
    const maxTotal = Math.max(1, ...totals);

    const tickCount = 5;
    const gridlines = [];
    for (let i = 0; i <= tickCount; i++) {
        const tickValue = Math.round((maxTotal * i) / tickCount);
        const y = paddingTop + chartHeight - (tickValue / maxTotal) * chartHeight;
        gridlines.push(`<line x1="${paddingX}" y1="${y}" x2="${width - paddingX}" y2="${y}" class="chart-gridline" />`);
        gridlines.push(`<text x="${paddingX - 6}" y="${y + 3.5}" class="chart-tick-label" text-anchor="end">${tickValue}</text>`);
    }

    const bars = data.map((item, index) => {
        const clubMatches = Number(item.club_matches) || 0;
        const individualMatches = Number(item.individual_matches) || 0;
        const total = clubMatches + individualMatches;
        const x = paddingX + index * (barWidth + 8);
        const totalHeight = (total / maxTotal) * chartHeight;
        const clubHeight = total > 0 ? (clubMatches / total) * totalHeight : 0;
        const individualHeight = totalHeight - clubHeight;
        const baseY = paddingTop + chartHeight;
        const tooltipText = `${formatShortDate(item.week_start)}: ${total} total (${clubMatches} club + ${individualMatches} individual)`;

        return `
            <g onmouseenter="showChartTooltip(event,'${tooltipText}')" onmouseleave="hideChartTooltip()" onclick="showChartTooltip(event,'${tooltipText}')" style="cursor:pointer">
                <rect x="${x}" y="${baseY - individualHeight}" width="${barWidth}" height="${individualHeight}" fill="#60a5fa" rx="2">
                    <title>${item.week_start}: ${individualMatches} partidos individuales</title>
                </rect>
                <rect x="${x}" y="${baseY - individualHeight - clubHeight}" width="${barWidth}" height="${clubHeight}" fill="#86efac" rx="2">
                    <title>${item.week_start}: ${clubMatches} partidos de club</title>
                </rect>
            </g>
        `;
    }).join('');

    const labels = data
        .map((item, index) => {
            const x = paddingX + index * (barWidth + 8) + barWidth / 2;
            return `<text x="${x}" y="${height - 8}" class="chart-axis-label" text-anchor="middle">${formatShortDate(item.week_start)}</text>`;
        })
        .join('');

    return `
        <svg class="svg-chart" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="Partidos semanales por tipo">
            ${gridlines.join('')}
            <line x1="${paddingX}" y1="${paddingTop + chartHeight}" x2="${width - paddingX}" y2="${paddingTop + chartHeight}" class="chart-axis" />
            ${bars}
            ${labels}
        </svg>
    `;
}

function createRetentionChart(data) {
    if (!Array.isArray(data) || data.length === 0) {
        return '<div class="chart-empty">Sin datos disponibles</div>';
    }

    const maxRate = 100;

    return `
        <div class="retention-bars">
            ${data
                .map((item) => {
                    const rate = Number(item.retention_rate) || 0;
                    return `
                        <div class="retention-row">
                            <div class="retention-label">${formatShortDate(item.cohort_week_start)}</div>
                            <div class="retention-track">
                                <div class="retention-fill" style="width: ${Math.min(Math.max(rate, 0), maxRate)}%;">
                                    <title>Semana ${item.cohort_week_start} · Cohorte: ${item.cohort_size} · Retenidos: ${item.retained_count}</title>
                                </div>
                            </div>
                            <div class="retention-value">${rate}%</div>
                        </div>
                    `;
                })
                .join('')}
        </div>
    `;
}

function renderDashboard(stats) {
    const app = document.getElementById('app');
    const totalPlayers = (stats.total_players_s5 || 0) + (stats.total_players_s10 || 0);
    const creatorStats = stats.match_creator_stats || {};
    const lastUsersDay = (stats.daily_new_users || []).slice(-1)[0];
    const users24h = lastUsersDay ? Number(lastUsersDay.count) || 0 : 0;
    const lastClubsDay = (stats.daily_new_clubs || []).slice(-1)[0];
    const clubs24h = lastClubsDay ? Number(lastClubsDay.count) || 0 : 0;

    app.innerHTML = `
        <div class="header">
            <div class="header-content">
                <div>
                    <h1 class="header-title">
                        ${createIcon('trending-up', 'metric-icon')}
                        App Usage Analytics
                    </h1>
                    <p class="header-subtitle">Análisis de comportamiento y engagement de usuarios</p>
                </div>
                <a href="/home" class="back-button">Volver a la aplicación</a>
            </div>
        </div>

        <div class="container">
            <div class="section-header">
                <h2 class="section-title">📈 Crecimiento</h2>
            </div>
            <div class="metrics-grid charts-grid">
                <div class="metric-card chart-card">
                    <div class="metric-header">
                        <div class="metric-header-left">
                            <h3 class="metric-title" id="users-chart-title">Usuarios nuevos por día</h3>
                            <span class="period-total" id="users-chart-total" style="color: #fb923c;">${users24h} usuario${users24h !== 1 ? 's' : ''} nuevo${users24h !== 1 ? 's' : ''} hoy</span>
                        </div>
                        <div class="chart-range-selector">
                            <button class="period-btn-users-chart active" data-days="1" onclick="changeUsersChartRange(1, this)">24h</button>
                            <button class="period-btn-users-chart" data-days="7" onclick="changeUsersChartRange(7, this)">7d</button>
                            <button class="period-btn-users-chart" data-days="30" onclick="changeUsersChartRange(30, this)">30d</button>
                            <button class="period-btn-users-chart" data-days="90" onclick="changeUsersChartRange(90, this)">90d</button>
                        </div>
                    </div>
                    <div id="users-chart-content">
                        <div class="chart-single-value"><p class="metric-value">${users24h}</p><p class="metric-subtitle">Usuarios nuevos hoy</p></div>
                    </div>
                </div>
                <div class="metric-card chart-card">
                    <div class="metric-header">
                        <div class="metric-header-left">
                            <h3 class="metric-title" id="clubs-chart-title">Clubes nuevos por día</h3>
                            <span class="period-total" id="clubs-chart-total" style="color: #818cf8;">${clubs24h} club${clubs24h !== 1 ? 'es' : ''} nuevo${clubs24h !== 1 ? 's' : ''} hoy</span>
                        </div>
                        <div class="chart-range-selector">
                            <button class="period-btn-clubs-chart active" data-days="1" onclick="changeClubsChartRange(1, this)">24h</button>
                            <button class="period-btn-clubs-chart" data-days="7" onclick="changeClubsChartRange(7, this)">7d</button>
                            <button class="period-btn-clubs-chart" data-days="30" onclick="changeClubsChartRange(30, this)">30d</button>
                            <button class="period-btn-clubs-chart" data-days="90" onclick="changeClubsChartRange(90, this)">90d</button>
                        </div>
                    </div>
                    <div id="clubs-chart-content">
                        <div class="chart-single-value"><p class="metric-value">${clubs24h}</p><p class="metric-subtitle">Clubes nuevos hoy</p></div>
                    </div>
                </div>
            </div>
            <div class="metrics-grid growth-cards-grid">
                <div class="metric-card compact-card">
                    <div class="metric-header">${createIcon('users', 'metric-icon')}</div>
                    <h3 class="metric-title">Total Usuarios</h3>
                    <p class="metric-value">${stats.total_users}</p>
                </div>
                <div class="metric-card compact-card">
                    <div class="metric-header">${createIcon('map-pin', 'metric-icon purple')}</div>
                    <h3 class="metric-title">Total Clubes</h3>
                    <p class="metric-value">${stats.total_clubs}</p>
                </div>
            </div>

            <div class="section-header">
                <h2 class="section-title">🔁 Retención y actividad reciente</h2>
            </div>
            <div class="metrics-grid no-stretch-grid">
                <div class="metric-card">
                    <div class="metric-header"><h3 class="metric-title">Usuarios activos por semana de registro</h3></div>
                    ${createRetentionChart(stats.cohort_retention || [])}
                </div>
                <div class="metric-card active-users-card">
                    <div class="metric-header">
                        <h3 class="metric-title">Usuarios activos recientes</h3>
                        <div class="chart-range-selector">
                            <button class="period-btn-active active" data-period="24h" onclick="changeActiveUsersPeriod('24h')">24h</button>
                            <button class="period-btn-active" data-period="7d" onclick="changeActiveUsersPeriod('7d')">7d</button>
                            <button class="period-btn-active" data-period="30d" onclick="changeActiveUsersPeriod('30d')">30d</button>
                        </div>
                    </div>
                    <p class="metric-value" id="active-users-value">${stats.active_users_24h}</p>
                    <p class="metric-subtitle" id="active-users-subtitle" style="color: #fb923c;">Últimas 24 horas</p>
                </div>
            </div>

            <div class="section-header">
                <h2 class="section-title">⚙️ Uso de features</h2>
            </div>
            <div class="metrics-grid">
                <div class="metric-card chart-card full-width-chart">
                    <div class="metric-header"><h3 class="metric-title">Partidos creados por semana</h3></div>
                    ${createStackedBarChart(stats.weekly_matches || [])}
                    <div class="chart-legend">
                        <span><span class="legend-dot legend-club"></span>Partidos de club</span>
                        <span><span class="legend-dot legend-individual"></span>Partidos individuales</span>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">${createIcon('trophy', 'metric-icon yellow')}</div>
                    <h3 class="metric-title">Partidos creados</h3>
                    <p class="metric-value">${creatorStats.total_matches || 0}</p>
                    <p class="metric-subtitle" style="color: #fbbf24;">registrados por ${creatorStats.distinct_creators || 0} usuarios distintos</p>
                </div>
                <div class="metric-card">
                    <div class="metric-header">${createIcon('user-check', 'metric-icon green')}</div>
                    <h3 class="metric-title">Creación de jugadores</h3>
                    <p class="metric-value">${stats.player_creation_rate}%</p>
                    <p class="metric-subtitle" style="color: #86efac;">${stats.users_with_players} usuarios con jugadores</p>
                </div>
                <div class="metric-card">
                    <div class="metric-header">${createIcon('zap', 'metric-icon blue')}</div>
                    <h3 class="metric-title">Comparación de escalas</h3>
                    <p class="metric-value">S5: ${stats.total_players_s5} / S10: ${stats.total_players_s10}</p>
                    <p class="metric-subtitle" style="color: #60a5fa;">${totalPlayers} jugadores en total</p>
                </div>
                <div class="metric-card">
                    <div class="metric-header">${createIcon('users', 'metric-icon blue')}</div>
                    <h3 class="metric-title">Participación en clubes</h3>
                    <p class="metric-value">${stats.club_participation_rate}%</p>
                    <p class="metric-subtitle" style="color: #60a5fa;">${stats.users_in_clubs} usuarios en clubes</p>
                </div>
            </div>
        </div>
    `;
}

function loadDashboard() {
    try {
        if (!dashboardStats) {
            throw new Error('No se han inicializado los datos del dashboard');
        }

        renderDashboard(dashboardStats);
    } catch (error) {
        console.error('Error cargando dashboard:', error);
        document.getElementById('app').innerHTML = `
            <div class="loading-screen">
                <p style="color: #ef4444; font-size: 1.25rem;">Error cargando los datos del dashboard</p>
                <p style="color: #94a3b8; margin-top: 0.5rem;">Por favor, intentá recargar la página</p>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});
