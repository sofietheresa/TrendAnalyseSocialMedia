# Dokumentation zur Social Media Trend Analysis

Dieses Verzeichnis enthält die Dokumentation zur Architektur und zum Aufbau der Social Media Trend Analysis Anwendung.

## Inhalt

- `architecture.md` - Markdown-Version der Architekturdokumentation
- `index.html` - HTML-Version der Dokumentation mit Styling für direkte Ansicht im Browser

## Verwendung

### HTML-Dokumentation anzeigen

Die HTML-Dokumentation kann direkt im Browser angezeigt werden. Öffnen Sie dazu die Datei `index.html` in einem beliebigen Webbrowser.

### In die Anwendung einbinden

Um die Dokumentation in die React-Anwendung einzubinden, können Sie die HTML-Datei direkt als statische Ressource verwenden:

```jsx
// Beispiel für eine Dokumentationskomponente
import React from 'react';

const Documentation = () => {
  return (
    <div className="documentation-container">
      <iframe 
        src="/doku/index.html" 
        title="Social Media Trend Analysis Documentation"
        width="100%" 
        height="800px" 
        style={{ border: 'none' }}
      />
    </div>
  );
};

export default Documentation;
```

## Aktualisierung

Um die Dokumentation zu aktualisieren, bearbeiten Sie entweder die Markdown-Datei `architecture.md` oder direkt die HTML-Datei `index.html`.

Bei umfangreicheren Änderungen empfiehlt es sich, zuerst die Markdown-Version zu aktualisieren und anschließend eine neue HTML-Version zu generieren. 