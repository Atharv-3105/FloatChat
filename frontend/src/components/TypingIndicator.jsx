import React from 'react';
import './TypingIndicator.css';

const TypingIndicator = () => {
  return (
    <div className="d-flex justify-content-start mb-3">
        <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
  );
};

export default TypingIndicator;
