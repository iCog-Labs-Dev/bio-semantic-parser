// frontend/src/App.jsx
import './App.css'; 
import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';

const backendUrl = process.env.REACT_APP_BACKEND_URL;
const backendWsUrl = process.env.REACT_APP_BACKEND_WS_URL;

  // private getAppUrl(req: Request): string {
  //   const env = process.env.NODE_ENV
  //   const protocol = 'https';
  //   const host = req.get('host');
  //   return `${protocol}://${host}/${env}`;
  // }

if (!backendUrl || !backendWsUrl) {
  console.error('REACT_APP_BACKEND_URL or REACT_APP_BACKEND_WS_URL is not defined in .env file');
  throw new Error('REACT_APP_BACKEND_URL or REACT_APP_BACKEND_WS_URL is not defined in .env file');
}

function App() {
  const [clientId] = useState(uuidv4());
  const [messages, setMessages] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [gseId, setGseId] = useState('');
  const [error, setError] = useState('');
  const [mettaCodeAbstract, setMettaCodeAbstract] = useState(null);
  const [mettaCodeGSE, setMettaCodeGSE] = useState(null);



  // Validation: Accept GSE followed by 1+ digits
  const isValidGseId = (id) => /^GSE\d+$/.test(id);

  //general error message
  const getGseError = (id) => {
    if (/^G$|^GS$|^GSE$/.test(id) || /^GSE\d*$/.test(id)) return ""; // Allow in-progress typing
    if (id === "") return "";
    return "Please enter a valid GEO Series ID starting with 'GSE' followed by digits (e.g., GSE12345).";
  };

  const startProcess = async () => {
    if (loading || !isValidGseId(gseId)) return;
    setLoading(true);
    setMessages([]);
    await fetch(`${backendUrl}/process?client_id=${clientId}&gse_id=${gseId}`, {
      method: 'POST',
    });
    // setLoading(false) will be called in ws.onmessage
  };

  const generateMeTTaCode = async (predicate_type, predicates) => {
    console.log('Generating MeTTa code for predicates');
    try {
     
      // console.log(predicates);
      const abstractContent=predicates
      const response = await fetch('http://localhost:8000/convert_fol_to_metta', {
        method: 'POST',
        headers: {
          'accept': 'application/json', 
          'Content-Type': 'text/plain',
        },
        body: abstractContent, // Send the abstract content directly as a string
      });

      if (!response.ok) {
        throw new Error('Failed to generate MeTTa code');
      }

      const data = await response.json();
      const rawMeTTa = Array.isArray(data.metta_valid)
        ? data.metta_valid.join(',')
        : data.metta_valid.toString();

      const formattedMeTTa = rawMeTTa.replace(/\),\(/g, ')\n(');

      if (predicate_type === "abstract_predicates") {
        setMettaCodeAbstract(formattedMeTTa || '');
      }
      else if (predicate_type === "gse_metadata_predicates") {
        setMettaCodeGSE(formattedMeTTa || '');
      }
      else {
        throw new Error('Unknown predicate type');
      }
      console.log(data.metta_valid)
    } catch (err) {
      console.error(err);
      alert('Error generating MeTTa code.');
    }
  };


  useEffect(() => {
    const ws = new WebSocket(`${backendWsUrl}/ws/${clientId}`);
    ws.onmessage = (event) => {
      const message = event.data;
      try {
        const json = JSON.parse(message);
        if (json.abstract && json.abstract_predicates && json.gse_metadata_predicates) {
          setResult(json);
          setLoading(false);
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
            placeholder={loading ? "Loading..." : "e.g., GSE12345"}
            value={gseId}
            onChange={(e) => {
              const upperValue = e.target.value.toUpperCase(); // Auto-format to uppercase
              setGseId(upperValue);
              setError(getGseError(upperValue));
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !loading && isValidGseId(gseId)) {
                startProcess();
              }
            }}
            disabled={loading}
          />
          {error && <div className="error-message">{error}</div>}
          <button
            className="button"
            id="fetch-btn"
            onClick={startProcess}
            disabled={loading || !isValidGseId(gseId)}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Loading...
              </>
            ) : (
              "Parse"
            )}
          </button>
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
          <div className="card-inner" style={{ flex: 1 }}>
            <div className="card-header">Abstract</div>
            <p>{result?.abstract || "\n\n \t Abstract will appear here once ready.\n\n"}</p>
          </div>
          <div className="card-inner" style={{ flex: 1 }}>
            <div className="card-header">Abstract Predicates</div>
            <p>{result?.abstract_predicates || "\n\n \t Abstract predicates will appear here once ready. \n\n"}</p>
            
            {result?.abstract_predicates && (
                <button className="button" 
                onClick={() => generateMeTTaCode("abstract_predicates",result.abstract_predicates)}
                >
                  Generate MeTTa Code
                </button>
              )}

              {mettaCodeAbstract && (
                  <div className="card" style={{ marginTop: '1rem' }}>
                    <div className="card-header">Generated MeTTa Code</div>
                    <pre className="metta-code"
                  onClick={() => {
                    navigator.clipboard.writeText(mettaCodeAbstract);
                    alert('MeTTa code copied to clipboard!');
                  }}
                  title="Click to copy"
                    >
                  <code>{mettaCodeAbstract}</code>
                </pre>
                  </div>
                )}



          </div>
          <div className="card-inner" style={{ flex: 1 }}>
            <div className="card-header">GSE Metadata Predicates</div>
            <p>{result?.gse_metadata_predicates || "\n\n \t GSE metadata predicates will appear here once ready. \n\n"}</p>
            {result?.gse_metadata_predicates && (
                <button className="button" 
                onClick={() => generateMeTTaCode("gse_metadata_predicates",result.gse_metadata_predicates)}
                >
                  Generate MeTTa Code
                </button>
              )}

              {mettaCodeGSE && (
                  <div className="card" style={{ marginTop: '1rem' }}>
                    <div className="card-header">Generated MeTTa Code</div>
                    <pre className="metta-code"
                  onClick={() => {
                    navigator.clipboard.writeText(mettaCodeGSE);
                    alert('MeTTa code copied to clipboard!');
                  }}
                  title="Click to copy"
                    >
                  <code>{mettaCodeGSE}</code>
                </pre>
                  </div>
                )}

          </div>
        </div>
      </div>
    </div>
  );
}

export default App;