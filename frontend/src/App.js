// frontend/src/App.jsx
import './App.css'; 
import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';

const backendUrl = process.env.REACT_APP_BACKEND_URL;
const backendWsUrl = process.env.REACT_APP_BACKEND_WS_URL;

if (!backendUrl || !backendWsUrl) {
  console.error('REACT_APP_BACKEND_URL or REACT_APP_BACKEND_WS_URL is not defined in .env file');
  throw new Error('REACT_APP_BACKEND_URL or REACT_APP_BACKEND_WS_URL is not defined in .env file');
}



function App() {
  const [clientId] = useState(uuidv4());
  const [messages, setMessages] = useState([]);
  const [result, setResult] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(`${backendWsUrl}/ws/${clientId}`);
    ws.onmessage = (event) => {
      const message = event.data;

  try {
    const json = JSON.parse(message);
    if (json.abstract && json.abstract_predicates && json.gse_metadata_predicates) {
      setResult(json);
    } else {
      setMessages((prev) => [...prev, message]);
    }
  } catch {
    // Not JSON, treat as progress update
    setMessages((prev) => [...prev, message]);
  }
};
    return () => ws.close();
  }, [clientId]);

  const [gseId, setGseId] = useState('');

  const startProcess = async () => {
    setMessages([]);
    await fetch(`${backendUrl}/process?client_id=${clientId}&gse_id=${gseId}`, {
      method: 'POST',
    });
  };

  return (
    <div className="app">
      <div className="sidebar">
        <div>
          <h1 className="title">Semantic Parser</h1>
          <p className="description">Enter a GSE ID to fetch and display annotations.</p>
          <input
            className="input"
            id="gse-id"
            name="gseId"
            type="text"
            placeholder="e.g., GSE12345"
            value={gseId}
            onChange={(e) => setGseId(e.target.value)}
          />
          <button className="button" id="fetch-btn" onClick={startProcess}>Parse</button>

          <div className="alert" style={{ display: 'none' }}>
            Connection error: Cannot reach server.
            <div className="card">
              <div className="card-header">Messages</div>
              <ul>
                {messages.map((msg, idx) => (<li key={idx}>{msg}</li>))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div className="main">
        <div className="card">
          <div className="card-header">Predicates & Progress</div>
          <div className="status-bar">{messages[messages.length - 1]}</div>
          <div className="progress-container">
            <div
              className="progress-bar"
              style={{
                width: `${Math.min((messages.length / 9) * 100, 100)}%`,
              }}
            ></div>
          </div>
          <div className="card" style={{ flex: 1 }}>
            <div className="card-header">Abstract</div>
            <p>{result?.abstract || "\n\n \t Abstract will appear here once ready.\n\n"}</p>
          </div>
          <div className="card" style={{ flex: 1 }}>
            <div className="card-header">Abstract Predicates</div>
            <p>{result?.abstract_predicates || "\n\n \t Abstract predicates will appear here once ready. \n\n"}</p>
          </div>
          <div className="card" style={{ flex: 1 }}>
            <div className="card-header">GSE Metadata Predicates</div>
            <p>{result?.gse_metadata_predicates || "\n\n \t GSE metadata predicates will appear here once ready. \n\n"}</p>
          </div>
        </div>
      </div>
    </div>
  );
  
}

export default App;