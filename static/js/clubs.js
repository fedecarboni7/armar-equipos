// Variables globales
let currentUser = null;
let clubId = null;
let pendingInvitations = [];
let clubMembers = [];
let pendingRoleChanges = new Map(); // Almacena los cambios pendientes

// Hacer variables accesibles globalmente
window.clubId = null;
window.currentUser = null;

function getCurrentClubData() {
  if (!window.clubId || window.clubId === 'my-players') {
    return null;
  }
  if (typeof getUserClubs !== 'function') {
    return null;
  }
  const clubs = getUserClubs();
  return clubs.find(club => club.id == window.clubId) || null;
}

// Función de utilidad para traducir roles
function translateRole(role) {
  switch (role) {
    case 'admin':
      return 'Administrador';
    case 'owner':
      return 'Dueño';
    case 'member':
      return 'Miembro';
    default:
      return role;
  }
}

// ==================== HELP MODAL (Clubs) ====================
const HELP_MODAL_CLUBS_KEY = 'clubs_helpModalShown';

function initClubsHelpModal() {
    const modal = document.getElementById('help-modal-clubs');
    const helpBtn = document.getElementById('help-btn');
    const closeBtn = document.getElementById('close-help-modal-clubs');
    const startBtn = document.getElementById('start-btn-clubs');
    if (!modal) return;

    // Mostrar modal si es la primera vez
    const hasSeenHelp = localStorage.getItem(HELP_MODAL_CLUBS_KEY);
    if (!hasSeenHelp) {
        showHelpModal();
    }

    // Event listeners
    helpBtn?.addEventListener('click', showHelpModal);
    closeBtn?.addEventListener('click', closeHelpModal);
    startBtn?.addEventListener('click', closeHelpModal);
    // Cerrar al hacer click fuera del contenido
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeHelpModal();
    });
    // Cerrar con Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) closeHelpModal();
    });

    function showHelpModal() {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeHelpModal() {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        localStorage.setItem(HELP_MODAL_CLUBS_KEY, 'true');
    }
}
// ==================== END HELP MODAL ====================

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
  // Inicializar modal de ayuda
  initClubsHelpModal();
  
  // Obtener datos del usuario desde el script element
  const currentUserData = document.getElementById('user-data');
  if (currentUserData) {
    try {
      currentUser = JSON.parse(currentUserData.textContent);
      window.currentUser = currentUser;
    } catch (error) {
      console.error('Error parsing user data:', error);
    }
  }
  
  // Obtener el club actual del selector
  const clubSelect = document.getElementById('club-select-navbar');
  if (clubSelect) {
    clubId = clubSelect.value !== 'my-players' ? clubSelect.value : null;
    window.clubId = clubId;
  }
  
  // Dar un pequeño delay para asegurar que todo esté listo
  setTimeout(() => {
    setupEventListeners();
    loadInvitations();
    if (clubId && clubId !== 'my-players') {
      loadClubMembers();
    }
  }, 100);
});

// Configuración de event listeners
function setupEventListeners() {
  // Botón de invitaciones - verificar que existe
  const invitationsBtn = document.getElementById('invitationsBtn');
  if (invitationsBtn) {
    invitationsBtn.addEventListener('click', () => openModal('invitationsModal'));
  }
  
  // Botón de eliminar club - verificar que existe
  const deleteClubBtn = document.getElementById('deleteClubBtn');
  if (deleteClubBtn) {
    deleteClubBtn.addEventListener('click', () => confirmDeleteClub());
  }

  // Cerrar modales con la tecla Escape
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      // Cerrar cualquier modal visible
      const visibleModals = document.querySelectorAll('.club-modal[style*="flex"]');
      visibleModals.forEach(modal => {
        modal.style.display = 'none';
      });
    }
  });

  // Cerrar modales al hacer click fuera (ya no es necesario porque está en las funciones individuales)
}

function showInviteContent() {
  document.getElementById('membersContent').style.display = 'none';
  document.getElementById('inviteContent').style.display = 'block';
  document.getElementById('inviteUsernameInput').value = ''; // Actualizado el ID
}

function showMembersContent() {
  document.getElementById('inviteContent').style.display = 'none';
  document.getElementById('membersContent').style.display = 'block';
}

// Funciones de UI
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = 'flex';
    
    // Cerrar modal al hacer click en el backdrop
    const backdrop = modal.querySelector('.modal-backdrop');
    if (backdrop) {
      backdrop.onclick = () => closeModal(modalId);
    }
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = 'none';
  }
}

// Funciones de carga de datos
function loadInvitations() {
  fetch('/invitations/pending', {
    method: 'GET',
    headers: {
      'Accept': 'application/json'
    }  
  })
  .then(response => response.json())
  .then(response => {
    pendingInvitations = response;
    updateInvitationsUI();
  })
  .catch(error => {
    console.error('Error al cargar invitaciones:', error);
  });
}

async function loadClubMembers() {
  if (!clubId) {
    return;
  }
  
  try {
    const response = await fetch(`/clubs/${clubId}/members`);
    if (response.ok) {
      clubMembers = await response.json();
      
      // Actualizar el rol del usuario actual basándose en los miembros del club
      if (currentUser && clubMembers) {
        const currentUserMember = clubMembers.find(member => 
          member.user_id === currentUser.id || member.user_id === currentUser.userId
        );
        if (currentUserMember) {
          currentUser.clubRole = currentUserMember.role;
          window.currentUser = currentUser;
        }
      }
      
      updateMembersTableUI();
      
      // Actualizar las estadísticas de la club-card y el rol mostrado
      if (typeof updateMemberStats === 'function') {
        updateMemberStats(clubMembers);
      }
      if (typeof updateRoleBasedActions === 'function') {
        updateRoleBasedActions();
      }
    } else {
      console.error('Error response:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('Error al cargar miembros:', error);
  }
}

// Funciones de actualización de UI
function updateInvitationsUI() {
  const badge = document.getElementById('invitationsBadge');
  const list = document.getElementById('invitationsList');
  
  badge.textContent = pendingInvitations.length;
  badge.style.display = pendingInvitations.length > 0 ? 'flex' : 'none';
  
  list.innerHTML = pendingInvitations.length > 0 
    ? pendingInvitations.map(inv => `
      <div class="invitation-card">
        <span>Unirse a ${inv.club_name}</span>
        <div>
          <button class="btn" onclick="respondToInvitation(${inv.id}, false)">Rechazar</button>
          <button class="btn btn-primary" onclick="respondToInvitation(${inv.id}, true)">Aceptar</button>
        </div>
      </div>
    `).join('')
    : '<p>No tenés invitaciones pendientes</p>';
}

function updateMembersTableUI() {
  const tbody = document.getElementById('membersTableBody');
  const canEdit = currentUser && (currentUser.clubRole === 'admin' || currentUser.clubRole === 'owner');
  
  tbody.innerHTML = clubMembers.map(member => `
    <tr class="${member.role === 'pending' ? 'pending-member' : ''}">
      <td>${member.username}</td>
      <td>
        ${member.role === 'pending' ? 
          'Invitado <span class="pending-badge">Pendiente</span>' : 
          canEdit ? `
            <select
              class="member-role-select"
              ${member.user_id === currentUser.userId ? 'disabled' : ''}
              onchange="handleRoleChange(${member.user_id}, this.value, '${member.role}')"
            >
              <option value="member" ${member.role === 'member' ? 'selected' : ''}>Miembro</option>
              <option value="admin" ${member.role === 'admin' ? 'selected' : ''}>Administrador</option>
              <option value="owner" ${member.role === 'owner' ? 'selected' : ''}>Dueño</option>
            </select>
          ` : translateRole(member.role)
        }
      </td>
      <td>
        ${member.role === 'pending' ? `
          <button class="btn btn-secondary" onclick="cancelInvitation(${member.id})">Cancelar</button>
        ` : 
          canEdit && member.user_id !== currentUser.userId ? 
          `<button class="btn btn-danger" onclick="removeMember(${member.user_id})">Eliminar</button>` 
          : ''
        }
      </td>
    </tr>
  `).join('');

  // Mostrar u ocultar el botón de confirmar según haya cambios pendientes
  const confirmButton = document.getElementById('confirmChangesBtn');
  if (confirmButton) {
    confirmButton.style.display = pendingRoleChanges.size > 0 ? 'block' : 'none';
  }
  
  // Mostrar u ocultar el botón de invitar según los permisos
  const inviteBtn = document.getElementById('inviteBtn');
  if (inviteBtn) {
    const canInvite = currentUser && (currentUser.clubRole === 'admin' || currentUser.clubRole === 'owner');
    inviteBtn.style.display = canInvite ? 'inline-flex' : 'none';
    
    // Asegurar que el event listener esté configurado
    if (canInvite && !inviteBtn.dataset.listenerAdded) {
      inviteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        showInviteContent();
      });
      inviteBtn.dataset.listenerAdded = 'true';
    }
  }
}

function handleRoleChange(userId, newRole, currentRole) {
  if (newRole !== currentRole) {
    pendingRoleChanges.set(userId, newRole);
  } else {
    pendingRoleChanges.delete(userId);
  }
  
  // Mostrar u ocultar el botón de confirmar
  const confirmButton = document.getElementById('confirmChangesBtn');
  confirmButton.style.display = pendingRoleChanges.size > 0 ? 'block' : 'none';
}

async function confirmRoleChanges() {
  if (pendingRoleChanges.size === 0) return;

  const confirmation = confirm('¿Confirmar los cambios de roles?');
  if (!confirmation) return;

  let success = true;
  
  for (const [userId, newRole] of pendingRoleChanges) {
    try {
      const response = await fetch(`/clubs/${clubId}/members/${userId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: newRole })
      });
      
      if (!response.ok) {
        success = false;
        const errorData = await response.json();
        alert(`Error al actualizar el rol: ${errorData.detail}`);
      }
    } catch (error) {
      success = false;
      console.error('Error:', error);
      alert('Error al actualizar el rol');
    }
  }

  if (success) {
    await loadClubMembers(); // Recargar la lista de miembros
    pendingRoleChanges.clear(); // Limpiar cambios pendientes
    const confirmButton = document.getElementById('confirmChangesBtn');
    confirmButton.style.display = 'none';
  }
}

// Funciones de acción
function sendInvitation() {
  const username = document.getElementById('inviteUsernameInput').value; // Actualizado el ID
  if (!username) {
    alert('Por favor ingresa un nombre de usuario');
    return;
  }
  
  fetch(`/clubs/${clubId}/invite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ invited_username: username })
    })
    .then(response => response.json().then(data => ({ status: response.status, body: data })))
    .then(({ status, body }) => {
      if (status === 200) {
        alert('Invitación enviada con éxito');
        showMembersContent(); // Volver a la vista de miembros
      } else {
        alert(`Error al enviar la invitación: ${body.detail}`);
      }
    })
    .catch (error => {
      console.error('Error:', error);
      alert('Error al enviar la invitación');
    });
}

async function respondToInvitation(invitationId, accept) {
  try {
    const response = await fetch(`/invitations/${invitationId}/${accept ? 'accept' : 'reject'}`, {
      method: 'POST'
    });
    
    if (response.ok) {
      pendingInvitations = pendingInvitations.filter(inv => inv.id !== invitationId);
      updateInvitationsUI();
      if (accept) {
        window.location.reload(); // Recargar para actualizar la UI con el nuevo club
      }
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Error al responder a la invitación');
  }
}

async function updateMemberRole(userId, newRole) {
  try {
    const response = await fetch(`/clubs/${clubId}/members/${userId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: newRole })
    });
    
    if (response.ok) {
      clubMembers = clubMembers.map(member =>
        member.user_id === userId ? { ...member, role: newRole } : member
      );
      updateMembersTableUI();
    } else {
      const errorData = await response.json();
      alert(`Error al actualizar el rol: ${errorData.detail}`);
      loadClubMembers();
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Error al actualizar el rol');
  }
}

async function removeMember(userId) {
  if (!confirm('¿Estás seguro de que deseas eliminar a este miembro?')) return;
  
  try {
    const response = await fetch(`/clubs/${clubId}/members/${userId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      clubMembers = clubMembers.filter(member => member.user_id !== userId);
      updateMembersTableUI();
    } else {
      const errorData = await response.json();
      alert(`Error al eliminar al miembro: ${errorData.detail}`);
      loadClubMembers();
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Error al eliminar al miembro');
  }
}

async function cancelInvitation(invitationId) {
  if (!confirm('¿Estás seguro de que deseas cancelar esta invitación?')) return;
  
  try {
    const response = await fetch(`/clubs/${clubId}/invitations/${invitationId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      await loadClubMembers(); // Reload the members list
    } else {
      const errorData = await response.json();
      alert(`Error al cancelar la invitación: ${errorData.detail}`);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Error al cancelar la invitación');
  }
}

function loadPlayersForClub() {
  const select = document.getElementById('club-select');
  const selectedValue = select.value;

  // Obtener la escala actual
  const currentScale = getCurrentScale();

  if (selectedValue === 'my-players') {
    window.location.href = `/home?scale=${currentScale}`;
    return;
  }

  // Navegar al club seleccionado preservando la escala
  window.location.href = `/home?club_id=${encodeURIComponent(selectedValue)}&scale=${currentScale}`;
}

// ========================================
// FUNCIONES DE BOTONES DE LA INTERFAZ
// ========================================

function openCreateClubModal() {
  const modal = document.getElementById('createClubModal');
  if (modal) {
    modal.style.display = 'flex';
    
    // Limpiar el input
    const nameInput = document.getElementById('new-club-name');
    if (nameInput) {
      nameInput.value = '';
      nameInput.focus();
    }
    
    // Cerrar modal al hacer click en el backdrop
    const backdrop = modal.querySelector('.modal-backdrop');
    if (backdrop) {
      backdrop.onclick = () => closeCreateClubModal();
    }
  }
}

function closeCreateClubModal() {
  const modal = document.getElementById('createClubModal');
  if (modal) {
    modal.style.display = 'none';
  }
}

async function createNewClub() {
  const nameInput = document.getElementById('new-club-name');
  const clubName = nameInput ? nameInput.value.trim() : '';
  
  if (!clubName || clubName.length < 3) {
    alert('El nombre del club debe tener al menos 3 caracteres');
    if (nameInput) nameInput.focus();
    return;
  }
  
  if (clubName.length > 50) {
    alert('El nombre del club no puede tener más de 50 caracteres');
    if (nameInput) nameInput.focus();
    return;
  }
  
  try {
    const response = await fetch('/clubs/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        name: clubName
      })
    });
    
    if (response.ok) {
      const newClub = await response.json();
      closeCreateClubModal();
      
      // Mostrar mensaje de éxito
      alert(`¡Club "${clubName}" creado exitosamente!`);
      
      // En lugar de recargar la página, actualizar el selector y cambiar al nuevo club
      if (typeof loadUserClubs === 'function') {
        await loadUserClubs();
        // Cambiar al nuevo club
        const selector = document.getElementById('club-select-navbar');
        if (selector) {
          selector.value = newClub.id;
          // Guardar en localStorage
          localStorage.setItem('selectedClubId', newClub.id);
          // Aplicar el cambio de contexto
          if (typeof onContextChanged === 'function') {
            onContextChanged(newClub.id);
          }
        }
      }
    } else {
      const error = await response.text();
      alert(`Error al crear el club: ${error}`);
    }
  } catch (error) {
    console.error('Error creating club:', error);
    alert('Error al crear el club. Intentá de nuevo.');
  }
}

function showInviteContent() {
  // Cambiar a la vista de invitar miembro en el modal de gestión
  const membersContent = document.getElementById('membersContent');
  const inviteContent = document.getElementById('inviteContent');
  
  if (membersContent && inviteContent) {
    membersContent.style.display = 'none';
    inviteContent.style.display = 'block';
  }
  
  // Si el modal no está abierto, abrirlo
  openModal('manageModal');
}

function showMembersContent() {
  const membersContent = document.getElementById('membersContent');
  const inviteContent = document.getElementById('inviteContent');
  
  if (membersContent && inviteContent) {
    membersContent.style.display = 'block';
    inviteContent.style.display = 'none';
  }
}

function confirmLeaveClub() {
  if (confirm('¿Estás seguro de que querés abandonar este club?')) {
    leaveClub();
  }
}

function confirmDeleteClub() {
  if (confirm('¿Estás seguro de que querés eliminar este club? Esta acción no se puede deshacer.')) {
    deleteClub();
  }
}

async function leaveClub() {
  if (!clubId) return;
  
  try {
    const response = await fetch(`/clubs/${clubId}/leave`, {
      method: 'POST',
      credentials: 'include'
    });
    
    if (response.ok) {
      alert('Saliste del club exitosamente');
      window.location.href = '/clubes';
    } else {
      const error = await response.text();
      alert(`Error al abandonar el club: ${error}`);
    }
  } catch (error) {
    console.error('Error leaving club:', error);
    alert('Error al abandonar el club. Intentá de nuevo.');
  }
}

async function deleteClub() {
  if (!clubId) return;
  
  try {
    const response = await fetch(`/clubs/${clubId}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    
    if (response.ok) {
      alert('Club eliminado exitosamente');
      window.location.href = '/clubes';
    } else {
      const error = await response.text();
      alert(`Error al eliminar el club: ${error}`);
    }
  } catch (error) {
    console.error('Error deleting club:', error);
    alert('Error al eliminar el club. Intentá de nuevo.');
  }
}
