/**
 * Skript zum Starten der Frontend-App mit direktem DB-Zugriff
 */

const { spawn } = require('child_process');
const path = require('path');

console.log('\n----- Social Media Trend Analysis - DB-Modus -----');
console.log('Starte Frontend mit direktem DB-Zugriff...\n');

// Setze Umgebungsvariablen für die API
process.env.REACT_APP_API_URL = 'http://localhost:8000';
process.env.REACT_APP_USE_MOCK_API = 'false';

// Starte die React-App
const reactApp = spawn('npm', ['run', 'start'], { 
  env: process.env,
  stdio: 'inherit',
  shell: process.platform === 'win32'
});

// Handler für Prozessbeendigung
const cleanup = () => {
  console.log('\n🛑 Beende Anwendung...');
  
  if (reactApp) {
    reactApp.kill();
  }
  
  process.exit();
};

// Höre auf Beendigungssignale
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

reactApp.on('exit', (code) => {
  console.log(`🌐 React App wurde mit Code ${code} beendet`);
  cleanup();
});

console.log('Frontend-Entwicklungs-Server gestartet.');
console.log('Verwende FastAPI-Backend auf: http://localhost:8000');
console.log('======================================================\n'); 