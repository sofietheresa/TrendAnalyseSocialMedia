import React, { useState, useEffect } from 'react';
import { Container, Tab, Tabs, Card, Table, Alert, Row, Col, Nav } from 'react-bootstrap';
import PresentationViewer from './PresentationViewer';
import './Documentation.css';

const Documentation = () => {
    const [activeTab, setActiveTab] = useState('overview');
    const [activeSubTab, setActiveSubTab] = useState('introduction');
    const [data, setData] = useState([]);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch data based on active tab
                if (activeTab === 'data') {
                    const response = await fetch('/api/analysis/data');
                    const result = await response.json();
                    setData(result);
                } else if (activeTab === 'logs') {
                    const response = await fetch('/api/logs');
                    const result = await response.json();
                    setLogs(result);
                }
                setLoading(false);
            } catch (err) {
                setError('Die Daten konnten nicht geladen werden. Es werden Beispieldaten verwendet.');
                // Use mock data for demo purposes
                if (activeTab === 'data') {
                    setData(getMockAnalysisData());
                } else if (activeTab === 'logs') {
                    setLogs(getMockLogs());
                }
                setLoading(false);
            }
        };

        // Only fetch if in data or logs tab
        if (activeTab === 'data' || activeTab === 'logs') {
            fetchData();
        } else {
            setLoading(false);
        }
    }, [activeTab]);

    const getMockAnalysisData = () => {
        return [
            { date: '2025-05-01', topic: 'KI-basierte Bildgenerierung', frequency: 145, sentiment: 'Positiv' },
            { date: '2025-05-01', topic: 'Virtual Reality Fitness', frequency: 98, sentiment: 'Neutral' },
            { date: '2025-05-01', topic: 'Nachhaltiges Gaming', frequency: 76, sentiment: 'Positiv' },
            { date: '2025-05-02', topic: 'Quantencomputer', frequency: 112, sentiment: 'Positiv' },
            { date: '2025-05-02', topic: 'KI-Ethik', frequency: 87, sentiment: 'Negativ' },
            { date: '2025-05-03', topic: 'Web3 Anwendungen', frequency: 65, sentiment: 'Neutral' }
        ];
    };

    const getMockLogs = () => {
        return [
            { timestamp: '2025-05-03T08:45:12', level: 'INFO', message: 'Reddit scraper started' },
            { timestamp: '2025-05-03T08:46:27', level: 'INFO', message: 'Found 234 unique posts from Reddit' },
            { timestamp: '2025-05-03T08:47:01', level: 'INFO', message: 'TikTok scraper started' },
            { timestamp: '2025-05-03T08:48:15', level: 'WARNING', message: 'Rate limit approaching for TikTok API' },
            { timestamp: '2025-05-03T08:49:32', level: 'INFO', message: 'Found 98 trending videos from TikTok' },
            { timestamp: '2025-05-03T08:50:12', level: 'INFO', message: 'YouTube scraper started' },
            { timestamp: '2025-05-03T08:51:45', level: 'INFO', message: 'Found 56 trending videos from YouTube' },
            { timestamp: '2025-05-03T08:52:17', level: 'INFO', message: 'Data preprocessing started' },
            { timestamp: '2025-05-03T08:55:01', level: 'INFO', message: 'Data preprocessing completed' },
            { timestamp: '2025-05-03T08:55:12', level: 'ERROR', message: 'Failed to connect to sentiment analysis service' }
        ];
    };

    const renderData = () => (
        <Card className="data-card">
            <Card.Body>
                <Table striped bordered hover responsive>
                    <thead>
                        <tr>
                            <th>Datum</th>
                            <th>Thema</th>
                            <th>Häufigkeit</th>
                            <th>Stimmung</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((item, index) => (
                            <tr key={index}>
                                <td>{new Date(item.date).toLocaleDateString('de-DE')}</td>
                                <td>{item.topic}</td>
                                <td>{item.frequency}</td>
                                <td>{item.sentiment}</td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            </Card.Body>
        </Card>
    );

    const renderLogs = () => (
        <Card className="logs-card">
            <Card.Body>
                <div className="logs-container">
                    {logs.map((log, index) => (
                        <div key={index} className={`log-entry log-${log.level.toLowerCase()}`}>
                            <span className="log-timestamp">{new Date(log.timestamp).toLocaleString('de-DE')}</span>
                            <span className="log-level">{log.level}</span>
                            <span className="log-message">{log.message}</span>
                        </div>
                    ))}
                </div>
            </Card.Body>
        </Card>
    );

    const renderPresentation = () => (
        <div className="presentation-wrapper">
            <PresentationViewer presentationUrl="/api/presentations/images" />
            <div className="presentation-info">
                <h4>Social Media Trend Analyse</h4>
                <p>Diese Präsentation bietet einen Überblick über unser Social Media Trend Analyse-Projekt, einschließlich der Methodik, wichtiger Erkenntnisse und zukünftiger Entwicklungen.</p>
            </div>
        </div>
    );

    const renderDocumentation = () => {
        switch(activeSubTab) {
            case 'introduction':
                return renderIntroduction();
            case 'installation':
                return renderInstallation();
            case 'usage':
                return renderUsage();
            case 'pipeline':
                return renderPipeline();
            case 'api':
                return renderAPI();
            default:
                return renderIntroduction();
        }
    };

    const renderIntroduction = () => (
        <div className="doc-content">
            <h3>Übersicht TrendAnalyseSocialMedia</h3>
            <p>
                TrendAnalyseSocialMedia ist eine umfassende Webanwendung zur Analyse von Trends in sozialen Medien. 
                Das System sammelt automatisch Daten von den größten Social-Media-Plattformen (Reddit, TikTok und YouTube), 
                verarbeitet diese mit einer ML-Pipeline und präsentiert die Ergebnisse in einem interaktiven Dashboard.
            </p>

            <h4>Hauptfunktionen</h4>
            <ul>
                <li><strong>Automatisiertes Scraping:</strong> Regelmäßiges Sammeln von Daten von Reddit, TikTok und YouTube</li>
                <li><strong>ML-Pipeline:</strong> Automatische Analyse von Textinhalten und Trendermittlung</li>
                <li><strong>Interaktives Dashboard:</strong> Visualisierung von Trends und Statistiken</li>
                <li><strong>Dokumentation:</strong> Umfassende Dokumentation und Präsentationsmöglichkeiten</li>
            </ul>

            <h4>Technologie-Stack</h4>
            <ul>
                <li><strong>Backend:</strong> Python, FastAPI, PostgreSQL</li>
                <li><strong>Frontend:</strong> React, Bootstrap</li>
                <li><strong>ML-Komponenten:</strong> pandas, scikit-learn, NLTK</li>
                <li><strong>Deployment:</strong> Railway</li>
            </ul>
        </div>
    );

    const renderInstallation = () => (
        <div className="doc-content">
            <h3>Installation und Einrichtung</h3>
            <p>
                Folgen Sie diesen Schritten, um das System lokal einzurichten und zu starten.
            </p>

            <h4>Voraussetzungen</h4>
            <ul>
                <li>Python 3.11+</li>
                <li>Node.js 16+</li>
                <li>PostgreSQL-Datenbank</li>
            </ul>

            <h4>Schritte zur Installation</h4>
            <ol>
                <li>
                    <strong>Repository klonen</strong>
                    <pre>git clone https://github.com/yourusername/TrendAnalyseSocialMedia.git
cd TrendAnalyseSocialMedia</pre>
                </li>
                <li>
                    <strong>Python-Umgebung einrichten</strong>
                    <pre>python -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate
pip install -r requirements.txt</pre>
                </li>
                <li>
                    <strong>Umgebungsvariablen konfigurieren</strong>
                    <p>Erstellen Sie eine <code>.env</code>-Datei im Hauptverzeichnis mit folgenden Einträgen:</p>
                    <pre>DATABASE_URL=postgresql://username:password@host:port/dbname
REDDIT_ID=your_reddit_client_id
REDDIT_SECRET=your_reddit_client_secret
YT_KEY=your_youtube_api_key
MS_TOKEN=your_tiktok_ms_token</pre>
                </li>
                <li>
                    <strong>Frontend-Abhängigkeiten installieren</strong>
                    <pre>cd frontend
npm install</pre>
                </li>
            </ol>
        </div>
    );

    const renderUsage = () => (
        <div className="doc-content">
            <h3>Verwendung der Anwendung</h3>
            <p>
                Diese Anleitung erklärt, wie Sie die verschiedenen Funktionen der TrendAnalyseSocialMedia-Anwendung nutzen können.
            </p>

            <h4>Starten der Anwendung</h4>
            <ol>
                <li>
                    <strong>Backend starten</strong>
                    <pre>make start
# Oder direkt:
uvicorn src.main:app --reload</pre>
                </li>
                <li>
                    <strong>Frontend starten</strong>
                    <pre>make start-frontend
# Oder direkt:
cd frontend && npm start</pre>
                </li>
            </ol>

            <h4>Dashboard verwenden</h4>
            <p>
                Das Dashboard bietet einen schnellen Überblick über die aktuellen Trends:
            </p>
            <ul>
                <li>Verwenden Sie die Plattform-Filter, um Daten nach Quelle zu filtern</li>
                <li>Passen Sie den Zeitraum über die Datum-Auswahl an</li>
                <li>Nutzen Sie die verschiedenen Visualisierungen, um Trends zu identifizieren</li>
            </ul>

            <h4>Daten-Ansicht</h4>
            <p>
                In der Daten-Ansicht können Sie die Rohdaten einsehen:
            </p>
            <ul>
                <li>Filtern Sie nach Plattform, Datum und Thema</li>
                <li>Sortieren Sie nach verschiedenen Kriterien</li>
                <li>Exportieren Sie die Daten als CSV oder JSON</li>
            </ul>

            <h4>ML-Pipeline verwenden</h4>
            <p>
                Die ML-Pipeline kann über die Pipeline-Verwaltung gesteuert werden:
            </p>
            <ul>
                <li>Starten Sie eine neue Pipeline-Ausführung</li>
                <li>Überwachen Sie den Status laufender Pipelines</li>
                <li>Sehen Sie sich Ergebnisse früherer Durchläufe an</li>
            </ul>
        </div>
    );

    const renderPipeline = () => (
        <div className="doc-content">
            <h3>ML-Pipeline Architektur</h3>
            <p>
                Die ML-Pipeline ist das Herzstück der Anwendung und verarbeitet die gesammelten Social-Media-Daten in mehreren Schritten.
            </p>

            <h4>Komponenten der Pipeline</h4>
            <ol>
                <li>
                    <strong>Datensammlung</strong>
                    <p>
                        Der erste Schritt sammelt Daten von verschiedenen Plattformen:
                    </p>
                    <ul>
                        <li><strong>Reddit:</strong> Sammelt Text-Posts aus populären Subreddits</li>
                        <li><strong>TikTok:</strong> Erfasst Trending-Videos und deren Metadaten</li>
                        <li><strong>YouTube:</strong> Sammelt Trending-Videos und deren Beschreibungen</li>
                    </ul>
                </li>
                <li>
                    <strong>Vorverarbeitung</strong>
                    <p>
                        Dieser Schritt bereitet die Rohdaten für die Analyse vor:
                    </p>
                    <ul>
                        <li>Textbereinigung (Stopwörter entfernen, Lemmatisierung, etc.)</li>
                        <li>Feature-Extraktion (z.B. Hashtags, Mentions, URLs)</li>
                        <li>Normalisierung numerischer Features</li>
                    </ul>
                </li>
                <li>
                    <strong>Datenexploration</strong>
                    <p>
                        Analysiert die vorverarbeiteten Daten statistisch:
                    </p>
                    <ul>
                        <li>Themenerkennung mittels Clustering</li>
                        <li>Sentimentanalyse von Texten</li>
                        <li>Identifikation von Schlüsselwörtern und Phrasen</li>
                    </ul>
                </li>
                <li>
                    <strong>Vorhersagen</strong>
                    <p>
                        Der letzte Schritt generiert Vorhersagen und Erkenntnisse:
                    </p>
                    <ul>
                        <li>Trendprognosen für die nächsten Tage</li>
                        <li>Identifikation aufkommender Themen</li>
                        <li>Visualisierung der Ergebnisse</li>
                    </ul>
                </li>
            </ol>

            <h4>Erweiterbarkeit</h4>
            <p>
                Die Pipeline ist modular aufgebaut und kann leicht erweitert werden:
            </p>
            <ul>
                <li>Neue Dataquellen können durch Implementierung eines Scrapers hinzugefügt werden</li>
                <li>Zusätzliche Analyse-Schritte können in die Pipeline integriert werden</li>
                <li>Modelle können ausgetauscht oder ergänzt werden</li>
            </ul>
        </div>
    );

    const renderAPI = () => (
        <div className="doc-content">
            <h3>API-Dokumentation</h3>
            <p>
                Die TrendAnalyseSocialMedia-Anwendung bietet eine umfassende API für die Integration mit anderen Systemen.
            </p>

            <h4>API-Endpunkte</h4>
            <Table striped bordered hover responsive>
                <thead>
                    <tr>
                        <th>Endpunkt</th>
                        <th>Methode</th>
                        <th>Beschreibung</th>
                        <th>Parameter</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>/api/analysis/data</code></td>
                        <td>GET</td>
                        <td>Ruft analysierte Daten ab</td>
                        <td>
                            <code>platform</code> (optional)<br/>
                            <code>start_date</code> (optional)<br/>
                            <code>end_date</code> (optional)
                        </td>
                    </tr>
                    <tr>
                        <td><code>/api/mlops/models/{model_name}/drift</code></td>
                        <td>GET</td>
                        <td>Ruft Modell-Drift-Metriken ab</td>
                        <td><code>model_name</code> (erforderlich)</td>
                    </tr>
                    <tr>
                        <td><code>/api/mlops/pipelines</code></td>
                        <td>GET</td>
                        <td>Ruft alle Pipelines ab</td>
                        <td>keine</td>
                    </tr>
                    <tr>
                        <td><code>/api/mlops/pipelines/{pipeline_id}</code></td>
                        <td>GET</td>
                        <td>Ruft Details zu einer bestimmten Pipeline ab</td>
                        <td><code>pipeline_id</code> (erforderlich)</td>
                    </tr>
                    <tr>
                        <td><code>/api/mlops/pipelines/{pipeline_id}/executions</code></td>
                        <td>GET</td>
                        <td>Ruft Ausführungen einer Pipeline ab</td>
                        <td><code>pipeline_id</code> (erforderlich)</td>
                    </tr>
                    <tr>
                        <td><code>/api/mlops/pipelines/{pipeline_id}/execute</code></td>
                        <td>POST</td>
                        <td>Führt eine Pipeline aus</td>
                        <td>
                            <code>pipeline_id</code> (erforderlich)<br/>
                            <code>parameters</code> (optional)
                        </td>
                    </tr>
                    <tr>
                        <td><code>/api/scraper-status</code></td>
                        <td>GET</td>
                        <td>Ruft den Status der Scraper ab</td>
                        <td>keine</td>
                    </tr>
                </tbody>
            </Table>

            <h4>Authentifizierung</h4>
            <p>
                Die API verwendet API-Schlüssel für die Authentifizierung. Fügen Sie den API-Schlüssel im Header Ihrer Anfrage hinzu:
            </p>
            <pre>X-API-Key: your_api_key</pre>

            <h4>Beispiel für API-Anfrage</h4>
            <pre>{`
// Beispiel: Abrufen von Analysedaten für YouTube von letzter Woche
fetch('/api/analysis/data?platform=youtube&start_date=2025-05-01&end_date=2025-05-07', {
  headers: {
    'X-API-Key': 'your_api_key'
  }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
            `}</pre>
        </div>
    );

    if (loading && activeTab !== 'overview' && activeTab !== 'presentation') return <div className="loading">Lade Daten...</div>;
    if (error && (activeTab === 'data' || activeTab === 'logs')) return <Alert variant="warning">{error}</Alert>;

    return (
        <Container className="documentation-container">
            <h2 className="documentation-title">Projektdokumentation</h2>
            <Tabs
                activeKey={activeTab}
                onSelect={(k) => setActiveTab(k)}
                className="documentation-tabs"
            >
                <Tab eventKey="overview" title="Dokumentation">
                    <Row className="mt-4">
                        <Col md={3}>
                            <Nav variant="pills" className="flex-column doc-nav" activeKey={activeSubTab} onSelect={setActiveSubTab}>
                                <Nav.Item>
                                    <Nav.Link eventKey="introduction">Einführung</Nav.Link>
                                </Nav.Item>
                                <Nav.Item>
                                    <Nav.Link eventKey="installation">Installation</Nav.Link>
                                </Nav.Item>
                                <Nav.Item>
                                    <Nav.Link eventKey="usage">Verwendung</Nav.Link>
                                </Nav.Item>
                                <Nav.Item>
                                    <Nav.Link eventKey="pipeline">ML-Pipeline</Nav.Link>
                                </Nav.Item>
                                <Nav.Item>
                                    <Nav.Link eventKey="api">API</Nav.Link>
                                </Nav.Item>
                            </Nav>
                        </Col>
                        <Col md={9}>
                            {renderDocumentation()}
                        </Col>
                    </Row>
                </Tab>
                <Tab eventKey="presentation" title="Präsentation">
                    {renderPresentation()}
                </Tab>
                <Tab eventKey="data" title="Analyse-Daten">
                    {renderData()}
                </Tab>
                <Tab eventKey="logs" title="System-Logs">
                    {renderLogs()}
                </Tab>
            </Tabs>
        </Container>
    );
};

export default Documentation; 