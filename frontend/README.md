# Social Media Trend Analysis - Frontend

This application provides a user interface for analyzing social media trends across multiple platforms (Reddit, TikTok, YouTube).

## Features

- Real-time trend analysis 
- Topic modeling with visualization
- ML pipeline monitoring and orchestration
- Social media data browser
- Mock data support for development without API dependencies

## Architecture

The application follows a modern ML OPS architecture:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Data Sources  │     │  ML Pipeline    │     │   Monitoring    │
│  ┌───────────┐  │     │  ┌───────────┐  │     │  ┌───────────┐  │
│  │  Reddit   │  │     │  │ Data Prep │  │     │  │ Prometheus│  │
│  └───────────┘  │     │  └───────────┘  │     │  └───────────┘  │
│  ┌───────────┐  │     │  ┌───────────┐  │     │  ┌───────────┐  │
│  │  TikTok   │──┼────▶│  │ Model     │──┼────▶│  │ Grafana   │  │
│  └───────────┘  │     │  │ Training  │  │     │  └───────────┘  │
│  ┌───────────┐  │     │  └───────────┘  │     │  ┌───────────┐  │
│  │  YouTube  │  │     │  ┌───────────┐  │     │  │ Logging   │  │
│  └───────────┘  │     │  │ Deployment│  │     │  └───────────┘  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         ▲                      ▲                       ▲
         │                      │                       │
         └──────────────────────┼───────────────────────┘
                                │
                     ┌─────────────────────┐
                     │  ZenML Orchestration│
                     │  ┌───────────────┐  │
                     │  │ Pipeline Mgmt │  │
                     │  └───────────────┘  │
                     │  ┌───────────────┐  │
                     │  │ Model Registry│  │
                     │  └───────────────┘  │
                     └─────────────────────┘
                                ▲
                                │
                     ┌─────────────────────┐
                     │   Frontend (React)  │
                     │  ┌───────────────┐  │
                     │  │ Visualization │  │
                     │  └───────────────┘  │
                     │  ┌───────────────┐  │
                     │  │ Dashboards    │  │
                     │  └───────────────┘  │
                     └─────────────────────┘
```

Key components:
- **Frontend**: React-based user interface with visualizations and dashboards
- **Orchestration**: ZenML for pipeline management and model registry
- **Monitoring**: Prometheus and Grafana for metrics collection and visualization
- **ML Pipeline**: Components for data preparation, model training, and deployment

## Repository

Find the source code on GitHub: [TrendAnalyseSocialMedia](https://github.com/SofiePischl/TrendAnalyseSocialMedia)

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm (v8 or higher)

### Installation

1. Clone the repository
2. Navigate to the frontend directory
3. Install dependencies:

```bash
npm install
```

### Running the Application

#### Smart Start with API Fallback (Recommended)

This option will automatically detect if the API is available and fall back to mock data if it's not:

```bash
npm run start:auto
```

#### Standard Start (Requires API Server)

If you want to connect to the real API server (which must be running):

```bash
npm start
```

#### Start with Mock Data

To always use mock data, regardless of API availability:

```bash
npm run start:with-mock
```

### Environment Configuration

The application uses the following environment variables:

- `REACT_APP_API_URL`: The URL of the API server (default: `http://localhost:8002`)
- `REACT_APP_MOCK_API_URL`: The URL of the mock API server (default: `http://localhost:3001`)
- `REACT_APP_USE_MOCK_API`: Set to `true` to force using mock data

## Development

### API Connection

The application is designed to work with or without the API server. When the API server is unavailable, it will automatically fall back to mock data. This allows for development and testing without requiring the full backend infrastructure.

### Mock Data

Mock data is located in `src/mock-api/data.js`. You can modify this file to test different scenarios.

### Proxy Configuration

API requests are automatically proxied to the appropriate server. In development, requests are first sent to the real API server, and if that fails, they're redirected to the mock API server.

## Deployment

To build the application for production:

```bash
npm run build
```

This will create a `build` directory with the compiled application.

## Environment Variables

The application can be configured using the following environment variables:

- `REACT_APP_API_URL`: The URL of the API server (default: `http://localhost:8002`)
- `REACT_APP_MOCK_API_URL`: The URL of the mock API server (default: `http://localhost:3001`)

## API Integration

The frontend communicates with a unified API that includes all required functionality:

- Core data endpoints (/api/...)
- ML operations endpoints (/api/mlops/...)

All API requests are sent to the URL specified in `REACT_APP_API_URL`, which defaults to `http://localhost:8002`. 