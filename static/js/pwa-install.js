let deferredPrompt;
let installButton;

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/service-worker.js', { scope: '/static/' })
      .then(registration => {
        console.log('Service Worker registrado con éxito:', registration);
      })
      .catch(error => {
        console.log('Error al registrar Service Worker:', error);
      });
  });
}

window.addEventListener('beforeinstallprompt', (e) => {
  installButton = document.getElementById('install-button');
  if (!installButton) {
    return;
  }

  e.preventDefault();
  deferredPrompt = e;

  showInstallPromotion();
});

function showInstallPromotion() {
  installButton = document.getElementById('install-button');
  if (installButton && installButton.style.display !== 'inline-block') {
    installButton.style.display = 'inline-block';
    installButton.addEventListener('click', installApp);
  }
}

async function installApp() {
  if (!deferredPrompt) {
    return;
  }
  
  deferredPrompt.prompt();
  
  const { outcome } = await deferredPrompt.userChoice;
  console.log(`Resultado de la instalación: ${outcome}`);
  
  deferredPrompt = null;
  
  if (installButton) {
    installButton.style.display = 'none';
  }
}

window.addEventListener('appinstalled', () => {
  console.log('PWA instalada con éxito');
  deferredPrompt = null;
});
