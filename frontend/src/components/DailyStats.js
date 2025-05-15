import React from 'react';
import { Card } from 'react-bootstrap';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const DailyStats = ({ stats }) => {
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('de-DE', { month: 'short', day: 'numeric' });
    };

    const prepareChartData = () => {
        const dates = [...new Set([
            ...stats.reddit.map(d => d.date),
            ...stats.tiktok.map(d => d.date),
            ...stats.youtube.map(d => d.date)
        ])].sort();

        return {
            labels: dates.map(formatDate),
            datasets: [
                {
                    label: 'Reddit Posts',
                    data: dates.map(date => {
                        const entry = stats.reddit.find(d => d.date === date);
                        return entry ? entry.count : 0;
                    }),
                    borderColor: '#FF4500',
                    backgroundColor: 'rgba(255, 69, 0, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'TikTok Videos',
                    data: dates.map(date => {
                        const entry = stats.tiktok.find(d => d.date === date);
                        return entry ? entry.count : 0;
                    }),
                    borderColor: '#00F2EA',
                    backgroundColor: 'rgba(0, 242, 234, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'YouTube Videos',
                    data: dates.map(date => {
                        const entry = stats.youtube.find(d => d.date === date);
                        return entry ? entry.count : 0;
                    }),
                    borderColor: '#FF0000',
                    backgroundColor: 'rgba(255, 0, 0, 0.1)',
                    tension: 0.4
                }
            ]
        };
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Tägliche Scraping-Statistiken'
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Anzahl der Posts/Videos'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Datum'
                }
            }
        }
    };

    return (
        <div className="daily-stats mt-4">
            <Card>
                <Card.Body>
                    <Card.Title>Tägliche Statistiken (letzte 7 Tage)</Card.Title>
                    <div className="chart-container">
                        <Line data={prepareChartData()} options={chartOptions} />
                    </div>
                </Card.Body>
            </Card>
        </div>
    );
};

export default DailyStats; 