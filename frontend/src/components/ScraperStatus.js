import React from 'react';
import { Card, Badge } from 'react-bootstrap';
import { formatDistanceToNow } from 'date-fns';
import { de } from 'date-fns/locale';

const ScraperStatus = ({ status }) => {
    const getStatusBadge = (running) => {
        return running ? (
            <Badge bg="success">Aktiv</Badge>
        ) : (
            <Badge bg="danger">Inaktiv</Badge>
        );
    };

    const formatLastUpdate = (lastUpdate) => {
        if (!lastUpdate) return 'Keine Updates';
        return `Vor ${formatDistanceToNow(new Date(lastUpdate), { locale: de })}`;
    };

    return (
        <div className="scraper-status">
            <h2 className="mb-4">Scraper Status</h2>
            <div className="d-flex justify-content-between">
                <Card className="status-card reddit-card">
                    <Card.Body>
                        <Card.Title>Reddit Scraper</Card.Title>
                        <div className="status-info">
                            <p>Status: {getStatusBadge(status.reddit.running)}</p>
                            <p>Posts: {status.reddit.total_posts}</p>
                            <p>Letztes Update: {formatLastUpdate(status.reddit.last_update)}</p>
                        </div>
                    </Card.Body>
                </Card>

                <Card className="status-card tiktok-card">
                    <Card.Body>
                        <Card.Title>TikTok Scraper</Card.Title>
                        <div className="status-info">
                            <p>Status: {getStatusBadge(status.tiktok.running)}</p>
                            <p>Videos: {status.tiktok.total_posts}</p>
                            <p>Letztes Update: {formatLastUpdate(status.tiktok.last_update)}</p>
                        </div>
                    </Card.Body>
                </Card>

                <Card className="status-card youtube-card">
                    <Card.Body>
                        <Card.Title>YouTube Scraper</Card.Title>
                        <div className="status-info">
                            <p>Status: {getStatusBadge(status.youtube.running)}</p>
                            <p>Videos: {status.youtube.total_posts}</p>
                            <p>Letztes Update: {formatLastUpdate(status.youtube.last_update)}</p>
                        </div>
                    </Card.Body>
                </Card>
            </div>
        </div>
    );
};

export default ScraperStatus; 