import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Spinner, Alert } from 'react-bootstrap';
import ScraperStatus from './ScraperStatus';
import DailyStats from './DailyStats';
import { fetchScraperStatus, fetchDailyStats } from '../services/api';

const Dashboard = () => {
    const [scraperStatus, setScraperStatus] = useState(null);
    const [dailyStats, setDailyStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('Fetching scraper status and daily stats');

            // Fetch data using our API service functions
            const statusData = await fetchScraperStatus();
            console.log('Received status data:', statusData);

            const statsData = await fetchDailyStats();
            console.log('Received stats data:', statsData);

            setScraperStatus(statusData);
            setDailyStats(statsData);
        } catch (err) {
            console.error('Error fetching data:', err);
            setError(`Fehler beim Laden der Daten: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // Refresh data every minute
        const interval = setInterval(fetchData, 60000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="loading-container d-flex justify-content-center align-items-center" style={{ minHeight: '200px' }}>
                <Spinner animation="border" role="status">
                    <span className="visually-hidden">Laden...</span>
                </Spinner>
            </div>
        );
    }

    if (error) {
        return (
            <div className="error-container">
                <Alert variant="danger">
                    <Alert.Heading>Fehler beim Laden der Daten</Alert.Heading>
                    <p>{error}</p>
                    <hr />
                    <div className="d-flex justify-content-end">
                        <button onClick={fetchData} className="btn btn-outline-danger">
                            Erneut versuchen
                        </button>
                    </div>
                </Alert>
            </div>
        );
    }

    return (
        <div className="dashboard">
            <h1 className="mb-4">Social Media Trend Analysis</h1>
            
            {/* Scraper Status Section */}
            {scraperStatus && <ScraperStatus status={scraperStatus} />}
            
            {/* Daily Statistics Section */}
            {dailyStats && <DailyStats stats={dailyStats} />}
            
            {/* Latest Content Section */}
            <h2 className="mt-4 mb-3">Neueste Inhalte</h2>
            <Row>
                <Col md={4}>
                    <Card className="platform-card reddit">
                        <Card.Header>Reddit</Card.Header>
                        <Card.Body>
                            <Card.Title>{scraperStatus?.reddit?.total_posts || 0} Posts</Card.Title>
                            <div className="platform-stats">
                                <p>Neueste Posts:</p>
                                {scraperStatus?.reddit?.posts?.slice(0, 3).map(post => (
                                    <div key={post.id} className="post-preview">
                                        <h6>{post.title}</h6>
                                        <small>Score: {post.score}</small>
                                    </div>
                                ))}
                            </div>
                        </Card.Body>
                    </Card>
                </Col>

                <Col md={4}>
                    <Card className="platform-card tiktok">
                        <Card.Header>TikTok</Card.Header>
                        <Card.Body>
                            <Card.Title>{scraperStatus?.tiktok?.total_posts || 0} Videos</Card.Title>
                            <div className="platform-stats">
                                <p>Trending Videos:</p>
                                {scraperStatus?.tiktok?.videos?.slice(0, 3).map(video => (
                                    <div key={video.id} className="post-preview">
                                        <h6>{video.description}</h6>
                                        <small>Likes: {video.likes}</small>
                                    </div>
                                ))}
                            </div>
                        </Card.Body>
                    </Card>
                </Col>

                <Col md={4}>
                    <Card className="platform-card youtube">
                        <Card.Header>YouTube</Card.Header>
                        <Card.Body>
                            <Card.Title>{scraperStatus?.youtube?.total_posts || 0} Videos</Card.Title>
                            <div className="platform-stats">
                                <p>Top Videos:</p>
                                {scraperStatus?.youtube?.videos?.slice(0, 3).map(video => (
                                    <div key={video.video_id} className="post-preview">
                                        <h6>{video.title}</h6>
                                        <small>Views: {video.view_count}</small>
                                    </div>
                                ))}
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default Dashboard; 