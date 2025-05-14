import React from 'react';
import { useData } from '../context/DataContext';
import { Card, Row, Col, Spinner } from 'react-bootstrap';

const Dashboard = () => {
    const { socialMediaData, loading, error } = useData();

    if (loading) {
        return (
            <div className="loading-container">
                <Spinner animation="border" role="status">
                    <span className="visually-hidden">Laden...</span>
                </Spinner>
            </div>
        );
    }

    if (error) {
        return (
            <div className="error-container">
                <p>Fehler beim Laden der Daten: {error}</p>
            </div>
        );
    }

    return (
        <div className="dashboard">
            <h1>Social Media Dashboard</h1>
            
            <Row>
                <Col md={4}>
                    <Card className="platform-card reddit">
                        <Card.Header>Reddit</Card.Header>
                        <Card.Body>
                            <Card.Title>{socialMediaData.reddit.length} Posts</Card.Title>
                            <div className="platform-stats">
                                <p>Neueste Posts:</p>
                                {socialMediaData.reddit.slice(0, 3).map(post => (
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
                            <Card.Title>{socialMediaData.tiktok.length} Videos</Card.Title>
                            <div className="platform-stats">
                                <p>Trending Videos:</p>
                                {socialMediaData.tiktok.slice(0, 3).map(video => (
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
                            <Card.Title>{socialMediaData.youtube.length} Videos</Card.Title>
                            <div className="platform-stats">
                                <p>Top Videos:</p>
                                {socialMediaData.youtube.slice(0, 3).map(video => (
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