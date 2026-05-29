import React from 'react';
import { Card } from 'react-bootstrap';

const Message = ({ role, text }) => {
  const isUser = role === 'user';

  return (
    <div className={`d-flex ${isUser ? 'justify-content-end' : 'justify-content-start'} mb-3`}>
      <Card
        bg={isUser ? 'primary' : 'light'}
        text={isUser ? 'white' : 'dark'}
        style={{ maxWidth: '80%' }}
 
        className="p-2"
      >
        {text}
      </Card>
    </div>
  );
};

export default Message;
