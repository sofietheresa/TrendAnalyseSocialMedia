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

  // Fetch slides from the presentation_images directory
  useEffect(() => {
    const fetchSlides = async () => {
      try {
        setLoading(true);
        
        // Use the presentationUrl from props to build the slide paths
        // This should point to the public/api/presentations/images directory
        
        // Create paths for the slides based on actual files found in public directory
        const slideNames = [];
        for (let i = 1; i <= 18; i++) { // We know there are 18 slides from the directory listing
          slideNames.push(`Slide${i}.PNG`);
        }
        
        const presentationImages = slideNames.map(name => `${presentationUrl}/${name}`);
        
        console.log("Loading presentation slides from:", presentationImages);
        setSlides(presentationImages);
      } catch (err) {
        console.error("Fehler beim Laden der Präsentation:", err);
        setError("Die Präsentation konnte nicht geladen werden. Bitte versuchen Sie es später erneut.");
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
        <p>Präsentation wird geladen...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="presentation-error">
        <p>{error}</p>
        <p>Hinweis: Um Präsentationen anzuzeigen, legen Sie Ihre Präsentationsbilder im Verzeichnis <code>docs/presentation_images/</code> ab.</p>
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
              alt={`Folie ${currentSlide + 1}`} 
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
            <p>Keine Folien verfügbar</p>
            <p>Legen Sie Ihre Präsentationsbilder im Verzeichnis <code>docs/presentation_images/</code> ab.</p>
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
            <img src={slide} alt={`Miniaturansicht ${index + 1}`} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default PresentationViewer; 