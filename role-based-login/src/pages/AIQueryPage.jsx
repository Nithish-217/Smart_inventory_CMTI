import React, { useState } from 'react';
import './OfficerDashboard.css';

export default function AIQueryPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleQuery = async () => {
    if (!query.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const sessionId = localStorage.getItem('session_id');
      const response = await fetch('http://localhost:8000/api/officer/ai-query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-session-id': sessionId || ''
        },
        body: JSON.stringify({ query })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setResult(data);
      } else {
        setError(data.error || 'Failed to process query');
      }
    } catch (err) {
      setError('Error connecting to server');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  };

  return (
    <div className="dashboard-container">
      <h1>AI Inventory Query</h1>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Ask questions about the inventory using natural language.
      </p>

      <div style={{ marginBottom: '20px' }}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="e.g., Show me all tools with quantity greater than 5"
          style={{
            width: '100%',
            minHeight: '100px',
            padding: '12px',
            borderRadius: '8px',
            border: '1px solid #ddd',
            fontSize: '14px',
            fontFamily: 'inherit',
            resize: 'vertical'
          }}
        />
      </div>

      <button
        onClick={handleQuery}
        disabled={loading}
        style={{
          padding: '12px 24px',
          backgroundColor: loading ? '#ccc' : '#667eea',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: loading ? 'not-allowed' : 'pointer',
          fontSize: '16px',
          fontWeight: 'bold'
        }}
      >
        {loading ? 'Processing...' : 'Ask AI'}
      </button>

      {error && (
        <div style={{
          marginTop: '20px',
          padding: '12px',
          backgroundColor: '#fee',
          border: '1px solid #fcc',
          borderRadius: '8px',
          color: '#c33'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={{
          marginTop: '20px',
          padding: '20px',
          backgroundColor: '#f5f5f5',
          borderRadius: '8px',
          border: '1px solid #ddd'
        }}>
          <h3 style={{ marginTop: 0 }}>Answer</h3>
          <p style={{ fontSize: '16px', lineHeight: '1.6' }}>{result.answer}</p>

          {result.data && result.data.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h4>Raw Data ({result.data.length} records)</h4>
              <div style={{
                maxHeight: '300px',
                overflow: 'auto',
                backgroundColor: 'white',
                padding: '10px',
                borderRadius: '4px',
                border: '1px solid #ddd'
              }}>
                <pre style={{ margin: 0, fontSize: '12px' }}>
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          <details style={{ marginTop: '15px' }}>
            <summary style={{ cursor: 'pointer', color: '#667eea' }}>View Generated SQL</summary>
            <pre style={{
              marginTop: '10px',
              padding: '10px',
              backgroundColor: '#f0f0f0',
              borderRadius: '4px',
              fontSize: '12px',
              overflow: 'auto'
            }}>
              {result.sql}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}
