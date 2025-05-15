# Zugriffsbeschränkung der Social Media Trend Analysis

Diese Dokumentation beschreibt, wie die Zugriffsbeschränkung für die Social Media Trend Analysis Anwendung implementiert wurde und wie autorisierte Benutzer Zugriff erhalten können.

## Funktionsweise

Die Anwendung ist durch eine einfache Token-basierte Zugangsbeschränkung geschützt. Bevor ein Benutzer auf die eigentliche Anwendung zugreifen kann, muss er sich zunächst authentifizieren. Dies kann auf zwei Arten geschehen:

1. **Passwort-Eingabe**: Der Benutzer kann das Passwort `mlops2025` eingeben.
2. **Autorisierter Link**: Der Benutzer kann einen speziellen Link mit einem Token verwenden.

Nach erfolgreicher Authentifizierung wird ein Token im lokalen Speicher des Browsers gespeichert, sodass der Benutzer beim nächsten Besuch nicht erneut das Passwort eingeben muss.

## Autorisierter Link

Der autorisierte Link für den Zugriff auf die Anwendung lautet:

```
https://yourappurl.com/?access=trend-analysis-access-2025
```

Dieser Link enthält das Zugriffstoken als URL-Parameter. Wenn ein Benutzer diesen Link verwendet, wird er automatisch authentifiziert und erhält Zugriff auf die Anwendung.

## Zugriffsschutz deaktivieren

Für Entwicklungszwecke kann der Zugriffsschutz deaktiviert werden, indem die `AccessGate`-Komponente aus der App.js entfernt wird.

## Passwort oder Token ändern

Um das Passwort oder das Token zu ändern, bearbeiten Sie die Datei `frontend/src/components/AccessGate.js`:

1. Ändern Sie `mlops2025` in ein neues Passwort
2. Ändern Sie `trend-analysis-access-2025` in ein neues Token

## Sicherheitshinweise

Diese Zugriffsschutzmethode bietet eine grundlegende Absicherung gegen unbefugten Zugriff, ist jedoch nicht für hochsensible Daten geeignet. In einer Produktionsumgebung mit sensiblen Daten sollten fortgeschrittenere Authentifizierungs- und Autorisierungsmechanismen implementiert werden, wie:

- OAuth 2.0
- JSON Web Tokens (JWT) mit kurzlebigen Tokens
- Serverseitige Authentifizierung
- HTTPS-Verschlüsselung

## Für Administratoren

### Benutzern Zugriff gewähren

Um einem neuen Benutzer Zugriff zu gewähren, haben Sie folgende Möglichkeiten:

1. **Teilen des Passworts**: Teilen Sie das Passwort `mlops2025` mit dem Benutzer.
2. **Teilen des autorisierten Links**: Senden Sie dem Benutzer den Link mit dem Zugriffstoken.

### Zugriff widerrufen

Um den Zugriff zu widerrufen, ändern Sie das Token und das Passwort in der `AccessGate.js`-Datei und stellen Sie die Anwendung neu bereit. Dadurch werden alle vorhandenen Token ungültig. 