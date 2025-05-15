# Social Media Trend Analysis - Frontend

This application provides a user interface for analyzing social media trends across multiple platforms (Reddit, TikTok, YouTube).

## Features

- Real-time trend analysis 
- Topic modeling with visualization
- ML pipeline monitoring and orchestration
- Social media data browser
- Mock data support for development without API dependencies

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

- `REACT_APP_API_URL`: The URL of the API server (default: `http://localhost:8000`)
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