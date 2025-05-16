import React, { useState, useEffect } from 'react';
import { Container, Tab, Tabs, Card, Table, Alert } from 'react-bootstrap';
import PresentationViewer from './PresentationViewer';
import './Documentation.css';

const Documentation = () => {
    const [activeTab, setActiveTab] = useState('presentation');
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
                setError('Failed to fetch data');
                setLoading(false);
            }
        };

        // Only fetch if not in presentation tab
        if (activeTab !== 'presentation') {
            fetchData();
        } else {
            setLoading(false);
        }
    }, [activeTab]);

    const renderData = () => (
        <Card className="data-card">
            <Card.Body>
                <Table striped bordered hover responsive>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Topic</th>
                            <th>Frequency</th>
                            <th>Sentiment</th>
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
            <PresentationViewer presentationUrl="/presentations/social_media_trends.pptx" />
            <div className="presentation-info">
                <h4>Social Media Trend Analysis</h4>
                <p>This presentation provides an overview of our social media trend analysis project, including methodology, key findings, and future directions.</p>
            </div>
        </div>
    );

    if (loading && activeTab !== 'presentation') return <div className="loading">Loading...</div>;
    if (error) return <Alert variant="danger">{error}</Alert>;

    return (
        <Container className="documentation-container">
            <h2 className="documentation-title">Project Documentation</h2>
            <Tabs
                activeKey={activeTab}
                onSelect={(k) => setActiveTab(k)}
                className="documentation-tabs"
            >
                <Tab eventKey="presentation" title="Presentation">
                    {renderPresentation()}
                </Tab>
                <Tab eventKey="data" title="Analysis Data">
                    {renderData()}
                </Tab>
                <Tab eventKey="logs" title="System Logs">
                    {renderLogs()}
                </Tab>
            </Tabs>
        </Container>
    );
};

export default Documentation; 