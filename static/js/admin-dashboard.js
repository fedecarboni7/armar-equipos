// Función para crear iconos SVG simplificados
function createIcon(name, className = '') {
    const iconMap = {
        'users': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="m22 21-3.5-3.5"/></svg>`,
        'user-check': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16,11 18,13 22,9"/></svg>`,
        'trophy': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55.47.98.97 1.21C12.04 18.75 13 20.24 13 22"/><path d="M14 14.66V17c0 .55-.47.98-.97 1.21C11.96 18.75 11 20.24 11 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/></svg>`,
        'zap': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><polygon points="13,2 3,14 12,14 11,22 21,10 12,10 13,2"/></svg>`,
        'clock': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>`,
        'trending-up': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><polyline points="22,7 13.5,15.5 8.5,10.5 2,17"/><polyline points="16,7 22,7 22,13"/></svg>`,
        'map-pin': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>`,
        'mail': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>`,
        'link': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>`,
        'alert': `<svg class="${className}" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3.05h16.94a2 2 0 0 0 1.71-3.05L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
    };
    return iconMap[name] || '';
}

// Variables globales para almacenar los datos del dashboard
let dashboardStats = null;


// Función para inicializar los datos del dashboard
function initializeDashboard(stats) {
    dashboardStats = stats;
}

// Función genérica para cambiar períodos de tiempo
function changePeriod(type, period) {
    const dataMap = {
        'users': {
            '24h': { 
                value: dashboardStats.new_users_24h, 
                label: 'Últimas 24 horas', 
                color: '#fb923c'
            },
            '7d': { 
                value: dashboardStats.new_users_week, 
                label: 'Últimos 7 días', 
                color: '#818cf8'
            },
            '30d': { 
                value: dashboardStats.new_users_month, 
                label: 'Últimos 30 días', 
                color: '#f472b6'
            }
        },
        'clubs': {
            '24h': { 
                value: dashboardStats.new_clubs_24h, 
                label: 'Últimas 24 horas', 
                color: '#fb923c'
            },
            '7d': { 
                value: dashboardStats.new_clubs_week, 
                label: 'Últimos 7 días', 
                color: '#818cf8'
            },
            '30d': { 
                value: dashboardStats.new_clubs_month, 
                label: 'Últimos 30 días', 
                color: '#f472b6'
            }
        },
        'active': {
            '24h': { 
                value: dashboardStats.active_users_24h, 
                label: 'Últimas 24 horas', 
                color: '#fb923c'
            },
            '7d': { 
                value: dashboardStats.active_users_7d, 
                label: 'Últimos 7 días', 
                color: '#818cf8'
            },
            '30d': { 
                value: dashboardStats.active_users_30d, 
                label: 'Últimos 30 días', 
                color: '#f472b6'
            }
        }
    };

    const data = dataMap[type]?.[period];
    if (!data) return;

    // Definir elementos según el tipo
    const elementIds = {
        'users': {
            value: 'new-users-value',
            subtitle: 'new-users-subtitle',
            buttons: '.period-btn'
        },
        'clubs': {
            value: 'new-clubs-value',
            subtitle: 'new-clubs-subtitle',
            buttons: '.period-btn-clubs'
        },
        'active': {
            value: 'active-users-period-value',
            subtitle: 'active-users-period-subtitle',
            buttons: '.period-btn-active'
        }
    };

    const elements = elementIds[type];
    if (!elements) return;

    // Actualizar contenido de la tarjeta
    const valueElement = document.getElementById(elements.value);
    const subtitleElement = document.getElementById(elements.subtitle);

    if (valueElement && subtitleElement) {
        valueElement.textContent = data.value;
        subtitleElement.textContent = data.label;
        subtitleElement.style.color = data.color;
    }

    // Actualizar botones activos
    document.querySelectorAll(elements.buttons).forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`${elements.buttons}[data-period="${period}"]`).classList.add('active');
}

// Funciones de interfaz (mantienen compatibilidad)
function changeNewUsersPeriod(period) {
    changePeriod('users', period);
}

function changeNewClubsPeriod(period) {
    changePeriod('clubs', period);
}

function changeActiveUsersPeriod(period) {
    changePeriod('active', period);
}

// Función principal para cargar y mostrar datos
function loadDashboard() {
    try {
        // Verificar que tenemos los datos
        if (!dashboardStats) {
            throw new Error('No se han inicializado los datos del dashboard');
        }
        
        // Renderizar el dashboard inmediatamente
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

// Función para renderizar el dashboard
function renderDashboard(stats) {
    const app = document.getElementById('app');
    
    app.innerHTML = `
        <!-- Header -->
        <div class="header">
            <div class="header-content">
                <div>
                    <h1 class="header-title">
                        ${createIcon('trending-up', 'metric-icon')}
                        App Usage Analytics
                    </h1>
                    <p class="header-subtitle">Análisis de comportamiento y engagement de usuarios</p>
                </div>
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div class="status-badge">
                        <div class="pulse-dot"></div>
                        ${stats.active_users} usuarios activos
                    </div>
                    <a href="/home" class="back-button">Volver a la aplicación</a>
                </div>
            </div>
        </div>

        <div class="container">
            <!-- SECCIÓN 1: Métricas de Usuarios -->
            <div class="section-header">
                <h2 class="section-title">👥 Métricas de Usuarios</h2>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('users', 'metric-icon')}
                    </div>
                    <h3 class="metric-title">Total Usuarios</h3>
                    <p class="metric-value">${stats.total_users}</p>
                    <p class="metric-subtitle" style="color: #93c5fd;">${stats.engagement_rate}% están activos</p>
                </div>                
                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('clock', 'metric-icon orange')}
                    </div>
                    <div class="period-selector">
                        <button class="period-btn active" data-period="24h" onclick="changeNewUsersPeriod('24h')">24h</button>
                        <button class="period-btn" data-period="7d" onclick="changeNewUsersPeriod('7d')">7d</button>
                        <button class="period-btn" data-period="30d" onclick="changeNewUsersPeriod('30d')">30d</button>
                    </div>
                    <h3 class="metric-title">Usuarios Nuevos</h3>
                    <p class="metric-value" id="new-users-value">${stats.new_users_24h}</p>
                    <p class="metric-subtitle" id="new-users-subtitle" style="color: #fb923c;">Últimas 24 horas</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('alert', 'metric-icon red')}
                    </div>
                    <h3 class="metric-title">Tasa de Abandono</h3>
                    <p class="metric-value">${stats.abandonment_rate}%</p>
                    <p class="metric-subtitle" style="color: #ef4444;">${stats.abandoned_users} usuarios sin jugadores</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('zap', 'metric-icon purple')}
                        <button type="button" class="tooltip-icon" aria-label="Usuario activo: ha modificado jugadores en el período">ℹ️</button>
                    </div>
                    <div class="period-selector">
                        <button class="period-btn-active" data-period="24h" onclick="changeActiveUsersPeriod('24h')">24h</button>
                        <button class="period-btn-active active" data-period="7d" onclick="changeActiveUsersPeriod('7d')">7d</button>
                        <button class="period-btn-active" data-period="30d" onclick="changeActiveUsersPeriod('30d')">30d</button>
                    </div>
                    <h3 class="metric-title">Usuarios Activos</h3>
                    <p class="metric-value" id="active-users-period-value">${stats.active_users_7d}</p>
                    <p class="metric-subtitle" id="active-users-period-subtitle" style="color: #d8b4fe;">Últimos 7 días</p>
                </div>
            </div>

            <!-- SECCIÓN 2: Métricas de Jugadores -->
            <div class="section-header">
                <h2 class="section-title">⚽ Métricas de Jugadores</h2>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('user-check', 'metric-icon green')}
                    </div>
                    <h3 class="metric-title">Creación de Jugadores</h3>
                    <p class="metric-value">${stats.player_creation_rate}%</p>
                    <p class="metric-subtitle" style="color: #86efac;">${stats.users_with_players} usuarios han creado jugadores</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('zap', 'metric-icon purple')}
                    </div>
                    <h3 class="metric-title">Promedio Jugadores</h3>
                    <p class="metric-value">${stats.avg_players_per_user}</p>
                    <p class="metric-subtitle" style="color: #d8b4fe;">Por usuario activo</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('trophy', 'metric-icon yellow')}
                    </div>
                    <h3 class="metric-title">Total de Jugadores</h3>
                    <p class="metric-value">${stats.total_players_s5 + stats.total_players_s10}</p>
                    <p class="metric-subtitle" style="color: #fbbf24;">En toda la app</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('map-pin', 'metric-icon blue')}
                    </div>
                    <h3 class="metric-title">Jugadores en Clubs</h3>
                    <p class="metric-value">${stats.players_in_clubs}</p>
                    <p class="metric-subtitle" style="color: #60a5fa;">${stats.players_without_club} sin club</p>
                </div>
            </div>

            <!-- SECCIÓN 3: Métricas de Clubes -->
            <div class="section-header">
                <h2 class="section-title">🏟️ Métricas de Clubes</h2>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('map-pin', 'metric-icon purple')}
                    </div>
                    <h3 class="metric-title">Total Clubes</h3>
                    <p class="metric-value">${stats.total_clubs}</p>
                    <p class="metric-subtitle" style="color: #d8b4fe;">Comunidades activas</p>
                </div>                
                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('clock', 'metric-icon')}
                    </div>
                    <div class="period-selector-clubs">
                        <button class="period-btn-clubs active" data-period="24h" onclick="changeNewClubsPeriod('24h')">24h</button>
                        <button class="period-btn-clubs" data-period="7d" onclick="changeNewClubsPeriod('7d')">7d</button>
                        <button class="period-btn-clubs" data-period="30d" onclick="changeNewClubsPeriod('30d')">30d</button>
                    </div>
                    <h3 class="metric-title">Clubes Nuevos</h3>
                    <p class="metric-value" id="new-clubs-value">${stats.new_clubs_24h}</p>
                    <p class="metric-subtitle" id="new-clubs-subtitle" style="color: #93c5fd;">Últimas 24 horas</p>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('users', 'metric-icon blue')}
                    </div>
                    <h3 class="metric-title">Promedio Usuarios</h3>
                    <p class="metric-value">${stats.avg_users_per_club}</p>
                    <p class="metric-subtitle" style="color: #60a5fa;">Por club</p>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('trophy', 'metric-icon yellow')}
                    </div>
                    <h3 class="metric-title">Participación en Clubes</h3>
                    <p class="metric-value">${stats.club_participation_rate}%</p>
                    <p class="metric-subtitle" style="color: #fbbf24;">${stats.users_in_clubs} usuarios en clubes</p>
                </div>

            </div>

            <!-- SECCIÓN 4: Invitaciones -->
            <div class="section-header">
                <h2 class="section-title">✉️ Invitaciones a Clubes</h2>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('mail', 'metric-icon')}
                    </div>
                    <h3 class="metric-title">Total Invitaciones</h3>
                    <p class="metric-value">${stats.pending_invitations + stats.accepted_invitations + stats.rejected_invitations}</p>
                    <p class="metric-subtitle" style="color: #93c5fd;">Desde el inicio</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('user-check', 'metric-icon green')}
                    </div>
                    <h3 class="metric-title">Tasa de Aceptación</h3>
                    <p class="metric-value">${stats.invitation_acceptance_rate}%</p>
                    <p class="metric-subtitle" style="color: #86efac;">${stats.accepted_invitations} aceptadas</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('clock', 'metric-icon orange')}
                    </div>
                    <h3 class="metric-title">Pendientes</h3>
                    <p class="metric-value">${stats.pending_invitations}</p>
                    <p class="metric-subtitle" style="color: #fb923c;">Esperando respuesta</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('alert', 'metric-icon')}
                    </div>
                    <h3 class="metric-title">Rechazadas</h3>
                    <p class="metric-value">${stats.rejected_invitations}</p>
                    <p class="metric-subtitle" style="color: #ef4444;">No aceptadas</p>
                </div>
            </div>

            <!-- SECCIÓN 5: Email -->
            <div class="section-header">
                <h2 class="section-title">📧 Confirmación de Email</h2>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('mail', 'metric-icon')}
                    </div>
                    <h3 class="metric-title">Tasa de Confirmación</h3>
                    <p class="metric-value">${stats.email_confirmation_rate}%</p>
                    <p class="metric-subtitle" style="color: #34d399;">${stats.users_email_confirmed} confirmados / ${stats.total_users - stats.users_email_confirmed} sin confirmar</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('link', 'metric-icon purple')}
                    </div>
                    <h3 class="metric-title">Resets de Contraseña</h3>
                    <p class="metric-value">${stats.total_password_resets}</p>
                    <p class="metric-subtitle" style="color: #d8b4fe;">${stats.users_with_reset} usuarios</p>
                </div>
            </div>

            <!-- SECCIÓN 6: Escalas S5 vs S10 -->
            <div class="section-header">
                <h2 class="section-title">📊 Adopción de Escalas</h2>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('trending-up', 'metric-icon')}
                    </div>
                    <h3 class="metric-title">Usuarios S5</h3>
                    <p class="metric-value">${stats.users_s5_only}</p>
                    <p class="metric-subtitle" style="color: #fbbf24;">Solo en S5</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('trending-up', 'metric-icon')}
                    </div>
                    <h3 class="metric-title">Usuarios S10</h3>
                    <p class="metric-value">${stats.users_s10_only}</p>
                    <p class="metric-subtitle" style="color: #60a5fa;">Solo en S10</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('trophy', 'metric-icon')}
                    </div>
                    <h3 class="metric-title">Ambas Escalas</h3>
                    <p class="metric-value">${stats.users_both_scales}</p>
                    <p class="metric-subtitle" style="color: #34d399;">Usando S5 y S10</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('zap', 'metric-icon')}
                    </div>
                    <h3 class="metric-title">Jugadores S5</h3>
                    <p class="metric-value">${stats.total_players_s5}</p>
                    <p class="metric-subtitle" style="color: #93c5fd;">Jugadores creados</p>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        ${createIcon('zap', 'metric-icon')}
                    </div>
                    <h3 class="metric-title">Jugadores S10</h3>
                    <p class="metric-value">${stats.total_players_s10}</p>
                    <p class="metric-subtitle" style="color: #34d399;">Jugadores creados</p>
                </div>
            </div>

            <!-- Insights finales -->
            <div class="insights">
                <div class="insights-card">
                    <h4 class="insights-title">💡 Insights Clave</h4>
                    <div class="insights-grid">
                        <p class="insight-purple">
                            <strong>${stats.engagement_rate}%</strong> de tus usuarios están creando contenido activamente
                        </p>
                        <p class="insight-green">
                            <strong>${stats.users_with_players}</strong> usuarios han creado jugadores para sus equipos
                        </p>
                        <p class="insight-yellow">
                            <strong>${stats.total_clubs}</strong> comunidades activas con <strong>${stats.avg_users_per_club}</strong> usuarios promedio por club
                        </p>
                        <p class="insight-blue">
                            <strong>${stats.new_users_month}</strong> nuevos usuarios este mes - Crecimiento del <strong>${Math.round((stats.new_users_month / stats.total_users) * 100)}%</strong>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Inicializar la aplicación cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
});