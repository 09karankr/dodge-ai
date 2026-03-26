import { useState, useRef, useEffect } from 'react';
import { User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  cypherQuery?: string;
}

interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (text: string) => void;
  onNodeClick: (id: string) => void;
  isLoading: boolean;
  width?: number;
}

const MessageComponent = ({ msg, onNodeClick }: { msg: ChatMessage, onNodeClick: (id: string) => void }) => {
  const [showQuery, setShowQuery] = useState(false);

  return (
    <div className={`msg-wrapper ${msg.sender}`}>
      <div className={`avatar ${msg.sender}`}>
        {msg.sender === 'bot' ? 'D' : <User size={20} strokeWidth={1.5} />}
      </div>
      <div className="msg-content">
        {msg.sender === 'bot' ? (
          <div className="msg-sender">
            Dodge AI <span>Graph Agent</span>
            {msg.cypherQuery && (
              <button
                className="show-query-btn"
                onClick={() => setShowQuery(!showQuery)}
                title="See Cypher Translation"
              >
                {showQuery ? 'Hide Query' : 'Show Query'}
              </button>
            )}
          </div>
        ) : (
          <div className="msg-sender" style={{ justifyContent: 'flex-end' }}>You</div>
        )}
        <div className="msg-text">
          {msg.sender === 'bot' ? (
            <ReactMarkdown
              components={{
                a: ({ node, ...props }) => {
                  const href = props.href || '';
                  const id = href.startsWith('id:') ? href.replace('id:', '') : href;
                  console.log("ChatPanel: Link captured for ID:", id);
                  return (
                    <span
                      className="entity-link highlight"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        onNodeClick(id);
                      }}
                    >
                      {props.children}
                    </span>
                  );
                }
              }}
            >
              {msg.text}
            </ReactMarkdown>
          ) : msg.text}

          {showQuery && msg.cypherQuery && (
            <div className="cypher-block">
              <div className="cypher-label">Graph Query (Cypher)</div>
              <code>{msg.cypherQuery}</code>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default function ChatPanel({ messages, onSend, onNodeClick, isLoading, width }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = () => {
    if (!input.trim() || isLoading) return;
    onSend(input.trim());
    setInput('');
  };

  return (
    <div className="chat-panel" style={{ width }}>
      <div className="chat-header">
        <h2>Chat with Graph</h2>
        <p>Order to Cash</p>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <MessageComponent key={msg.id} msg={msg} onNodeClick={onNodeClick} />
        ))}
        {isLoading && (
          <div className="msg-wrapper bot">
            <div className="avatar bot">D</div>
            <div className="msg-content">
              <div className="msg-sender">Dodge AI <span>Graph Agent</span></div>
              <div className="msg-text" style={{ fontStyle: 'italic', opacity: 0.7 }}>Analyzing flow...</div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <div className="input-status">
          <div className="status-dot" style={{ background: isLoading ? '#f59e0b' : '#22c55e' }}></div>
          Dodge AI is {isLoading ? 'analyzing data...' : 'awaiting instructions'}
        </div>
        <div className="chat-input-area">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder="Analyze anything"
            disabled={isLoading}
          />
          <button className="chat-submit" onClick={handleSubmit} disabled={!input.trim() || isLoading}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
