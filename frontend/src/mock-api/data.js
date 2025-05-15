/**
 * Mock data module for the social media trend analysis application
 * This provides fallback data when the real API is unavailable
 */

// Mock Reddit data
const redditMockData = [
  {
    id: 'mock-reddit-1',
    title: 'New AI developments in healthcare',
    text: 'Researchers have developed new AI models that can predict patient outcomes with 95% accuracy.',
    author: 'AIResearcher',
    created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    url: 'https://reddit.com/r/technology/mock1',
    scraped_at: new Date().toISOString()
  },
  {
    id: 'mock-reddit-2',
    title: 'Climate change affects marine life',
    text: 'A new study shows how rising ocean temperatures are affecting marine ecosystems worldwide.',
    author: 'OceanScientist',
    created_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
    url: 'https://reddit.com/r/science/mock2',
    scraped_at: new Date().toISOString()
  },
  {
    id: 'mock-reddit-3',
    title: 'Tech companies shift to remote work permanently',
    text: 'Major tech companies announce permanent remote work options for all employees.',
    author: 'TechTrends',
    created_at: new Date(Date.now() - 10800000).toISOString(), // 3 hours ago
    url: 'https://reddit.com/r/technology/mock3',
    scraped_at: new Date().toISOString()
  }
];

// Mock TikTok data
const tiktokMockData = [
  {
    id: 'mock-tiktok-1',
    text: 'Check out this amazing AI art generation #AI #art #technology',
    author: 'techart_creator',
    created_at: new Date(Date.now() - 5400000).toISOString(), // 1.5 hours ago
    url: 'https://tiktok.com/@techart_creator/mock1',
    scraped_at: new Date().toISOString()
  },
  {
    id: 'mock-tiktok-2',
    text: 'How climate change is affecting our daily lives #climate #awareness',
    author: 'climate_awareness',
    created_at: new Date(Date.now() - 9000000).toISOString(), // 2.5 hours ago
    url: 'https://tiktok.com/@climate_awareness/mock2',
    scraped_at: new Date().toISOString()
  },
  {
    id: 'mock-tiktok-3',
    text: 'Remote work productivity hacks that actually work #remotework #productivity',
    author: 'productivity_tips',
    created_at: new Date(Date.now() - 12600000).toISOString(), // 3.5 hours ago
    url: 'https://tiktok.com/@productivity_tips/mock3',
    scraped_at: new Date().toISOString()
  }
];

// Mock YouTube data
const youtubeMockData = [
  {
    id: 'mock-youtube-1',
    title: 'The Future of AI in Healthcare: A Deep Dive',
    text: 'This video explores how AI is transforming healthcare through predictive analytics and personalized medicine.',
    author: 'Tech Insights',
    created_at: new Date(Date.now() - 4500000).toISOString(), // 1.25 hours ago
    url: 'https://youtube.com/watch?v=mock1',
    scraped_at: new Date().toISOString(),
    trending_date: new Date().toISOString().split('T')[0]
  },
  {
    id: 'mock-youtube-2',
    title: 'Climate Change: The Hidden Effects You Don\'t See',
    text: 'An in-depth look at the less obvious impacts of climate change on ecosystems and human society.',
    author: 'Science Explained',
    created_at: new Date(Date.now() - 8100000).toISOString(), // 2.25 hours ago
    url: 'https://youtube.com/watch?v=mock2',
    scraped_at: new Date().toISOString(),
    trending_date: new Date().toISOString().split('T')[0]
  },
  {
    id: 'mock-youtube-3',
    title: 'Remote Work Revolution: How Companies Are Adapting',
    text: 'This documentary examines how major tech companies are restructuring their operations for a remote-first world.',
    author: 'Business Trends',
    created_at: new Date(Date.now() - 11700000).toISOString(), // 3.25 hours ago
    url: 'https://youtube.com/watch?v=mock3',
    scraped_at: new Date().toISOString(),
    trending_date: new Date().toISOString().split('T')[0]
  }
];

// Map of platform to mock data
const mockDataMap = {
  reddit: redditMockData,
  tiktok: tiktokMockData,
  youtube: youtubeMockData
};

/**
 * Get mock data for a specific platform
 * @param {string} platform - The platform to get data for (reddit, tiktok, youtube)
 * @param {number} limit - The maximum number of items to return
 * @returns {Array} Array of mock data items
 */
export const getMockData = (platform, limit = 10) => {
  const data = mockDataMap[platform.toLowerCase()] || [];
  return data.slice(0, limit);
};

/**
 * Get all available mock data
 * @returns {Object} Object containing mock data for all platforms
 */
export const getAllMockData = () => {
  return mockDataMap;
};

export default {
  getMockData,
  getAllMockData
}; 