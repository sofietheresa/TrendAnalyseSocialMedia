import React, { useState, useEffect, useRef } from 'react';
import './PresentationViewer.css';

const PresentationViewer = ({ presentationUrl }) => {
  const [slides, setSlides] = useState([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const touchStartX = useRef(null);
  const touchEndX = useRef(null);
  const slideRef = useRef(null);

  // Simulated function to fetch slides
  // In production, you'd convert your PowerPoint to images or use a service like Google Slides embed
  useEffect(() => {
    const fetchSlides = async () => {
      try {
        setLoading(true);
        // For demo purposes, we'll use placeholder images
        // In production, you'd fetch actual slide images from your API
        const demoSlides = [
          '/presentation/slide1.jpg',
          '/presentation/slide2.jpg',
          '/presentation/slide3.jpg',
          '/presentation/slide4.jpg',
          '/presentation/slide5.jpg',
        ];
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        setSlides(demoSlides);
      } catch (err) {
        console.error("Error loading presentation:", err);
        setError("Failed to load presentation. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchSlides();
  }, [presentationUrl]);

  const goToNextSlide = () => {
    if (currentSlide < slides.length - 1) {
      setCurrentSlide(currentSlide + 1);
    }
  };

  const goToPrevSlide = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    }
  };

  // Touch event handlers for swipe functionality
  const handleTouchStart = (e) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e) => {
    touchEndX.current = e.changedTouches[0].clientX;
    handleSwipe();
  };

  const handleSwipe = () => {
    if (!touchStartX.current || !touchEndX.current) return;
    
    const diff = touchStartX.current - touchEndX.current;
    const threshold = 50; // Minimum swipe distance
    
    if (diff > threshold) {
      // Swiped left, go to next slide
      goToNextSlide();
    } else if (diff < -threshold) {
      // Swiped right, go to previous slide
      goToPrevSlide();
    }
    
    // Reset touch positions
    touchStartX.current = null;
    touchEndX.current = null;
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight') {
        goToNextSlide();
      } else if (e.key === 'ArrowLeft') {
        goToPrevSlide();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [currentSlide, slides.length]);

  // Add animation when changing slides
  useEffect(() => {
    if (slideRef.current) {
      slideRef.current.classList.add('slide-transition');
      const timeout = setTimeout(() => {
        if (slideRef.current) {
          slideRef.current.classList.remove('slide-transition');
        }
      }, 300);
      return () => clearTimeout(timeout);
    }
  }, [currentSlide]);

  if (loading) {
    return (
      <div className="presentation-loading">
        <div className="presentation-spinner"></div>
        <p>Loading presentation...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="presentation-error">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="presentation-viewer">
      <div 
        className="slide-container"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        ref={slideRef}
      >
        {slides.length > 0 ? (
          <>
            <img 
              src={slides[currentSlide]} 
              alt={`Slide ${currentSlide + 1}`} 
              className="slide-image"
            />
            <div className="slide-controls">
              <button 
                className="slide-button prev-button"
                onClick={goToPrevSlide}
                disabled={currentSlide === 0}
              >
                &#10094;
              </button>
              <div className="slide-indicator">
                {currentSlide + 1} / {slides.length}
              </div>
              <button 
                className="slide-button next-button"
                onClick={goToNextSlide}
                disabled={currentSlide === slides.length - 1}
              >
                &#10095;
              </button>
            </div>
          </>
        ) : (
          <div className="no-slides-message">
            No slides available
          </div>
        )}
      </div>
      
      <div className="slide-thumbnails">
        {slides.map((slide, index) => (
          <div 
            key={index} 
            className={`slide-thumbnail ${index === currentSlide ? 'active' : ''}`}
            onClick={() => setCurrentSlide(index)}
          >
            <img src={slide} alt={`Thumbnail ${index + 1}`} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default PresentationViewer; 