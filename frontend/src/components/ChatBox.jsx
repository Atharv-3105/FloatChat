import { useState, useEffect, useRef } from "react";
import { Form, Button, InputGroup, Spinner } from "react-bootstrap";
import Message from "./Message";

export default function ChatBox({ onResponse, loading, setLoading, setError }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendQuery = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", text: input };
    // Add user message and a placeholder for the bot's response
    setMessages((prev) => [...prev, userMessage, { role: "assistant", text: "..." }]);
    
    setLoading(true);
    setError(null);
    onResponse(null);
    setInput("");

    try {
      const res = await fetch("http://localhost:8000/api/v1/queries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: input, model: "gemini" }),
      });

      if (!res.ok) {
        // Try to get error details from the backend response
        const errorData = await res.json().catch(() => null);
        const detail = errorData?.detail || `HTTP error! status: ${res.status}`;
        throw new Error(detail);
      }

      const data = await res.json();

      onResponse(data); // Pass the whole response object to the parent
      setMessages(prev => prev.map((msg, index) =>
        index === prev.length - 1 ? { ...msg, text: data.answer || "Here are the results." } : msg
      ));

    } catch (err) {
      const errorText = err.message || "Failed to connect to the server. Please try again.";
      setError(errorText);
      setMessages(prev => prev.map((msg, index) =>
        index === prev.length - 1 ? { ...msg, text: errorText } : msg
      ));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      sendQuery();
    }
  };

  return (
    <div className="d-flex flex-column h-100">
      {/* Messages */}
      <div className="flex-grow-1 p-3" style={{ overflowY: "auto" }}>
        {messages.map((msg, i) => (
          <Message key={i} role={msg.role} text={msg.text} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3">
        <InputGroup>
          <Form.Control
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask something..."
            disabled={loading}
          />
          <Button onClick={sendQuery} disabled={loading}>
            {loading ? <Spinner as="span" animation="border" size="sm" /> : "Send"}
          </Button>
        </InputGroup>
      </div>
    </div>
  );
}