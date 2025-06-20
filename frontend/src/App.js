// frontend/src/App.jsx
import './App.css'; 
import { useState, useEffect, useRef } from 'react';
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
  // const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [abstract, setAbstract] = useState('');
  const [abstractPredicates, setAbstractPredicates] = useState('');
  const [gseMetadataPredicates, setGseMetadataPredicates] = useState('');
  const [gseId, setGseId] = useState('');
  const [error, setError] = useState('');
  const [mettaCodeAbstract, setMettaCodeAbstract] = useState(null);
  const [mettaCodeGSE, setMettaCodeGSE] = useState(null);
  const [mettaCodeGSM, setMettaCodeGSM] = useState(null);
  const [gsmList, setGsmList] = useState([]);
  const [selectedGsm, setSelectedGsm] = useState('');
  const [dropdownEnabled, setDropdownEnabled] = useState(false);
  const [gsmTableData, setGsmTableData] = useState(null);
  const tableRef = useRef(null);


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
      const response = await fetch('http://localhost:8000/get_gsm', {
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

       if (json.gsms) {
        console.log("Received GSMs:", json.gsms);
        setGsmList(json.gsms.gsm_ids);
        setDropdownEnabled(true);
        setSelectedGsm('');
      }

      if (json.abstract) {
        setAbstract(json.abstract);
      }

      if (json.abstract_predicates) {
        setAbstractPredicates(json.abstract_predicates);
      }

      if (json.gse_metadata_predicates) {
        setGseMetadataPredicates(json.gse_metadata_predicates);
        setLoading(false); // Loading ends after GSE metadata is received
      }


      // If none of the expected fields exist, treat as plain message
      if (!json.abstract && !json.abstract_predicates && !json.gse_metadata_predicates) {
        setMessages((prev) => [...prev, message]);
      }

    } catch {
      // Not JSON, treat as progress update
      setMessages((prev) => [...prev, message]);
    }
  };

  return () => ws.close();
}, [clientId]);

// The handler for GSM selection
const fetchGsmData = async (gsmId) => {
  try {
    const response = await fetch(`http://localhost:8000/get_gsm?gse_id=${gseId}&gsm_id=${gsmId}`, {
      method: 'POST',
      headers: {
          'accept': 'application/json', 
          'Content-Type': 'text/plain',
        },
    });

    if (!response.ok) throw new Error('Failed to fetch GSM data');

    const data = await response.json();

    // Save GSM table data (assuming this is the main response structure)
    setGsmTableData(data);

    // Scroll into view
    console.log(gsmTableData);
    
    setTimeout(() => {
      if (tableRef.current) {
        tableRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);

  } catch (error) {
    console.error(error);
    alert('Error fetching GSM data');
  }
};

const generateMeTTaCodeForGsm = async () => {
  try {
    const gsmId = selectedGsm;
    const response = await fetch(`http://localhost:8000/gsm_to_metta?gse_id=${gseId}&gsm_id=${gsmId}`, {
      method: 'POST',
      headers: {
          'accept': 'application/json', 
          'Content-Type': 'text/plain',
        },
    });

    if (!response.ok) throw new Error('Failed to fetch GSM data');

    const gsmMetta = await response.json();
    setMettaCodeGSM(gsmMetta.table_metta || []);

  }
  catch (error) {
    console.error(error);
    alert('Error generating MeTTa code for GSM data');
  }
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

        {dropdownEnabled && gsmList.length > 0 && (
  <div className="card" style={{ marginTop: '1rem' }}>
    <div className="card-header">Select GSM</div>
    
    <select
      className="input"
      value={selectedGsm}
      onChange={(e) => {
        setSelectedGsm(e.target.value);
        fetchGsmData(e.target.value);
      }}
    >
      <option value="" disabled>Select a GSM ID</option>
      {gsmList.map((gsm, idx) => (
        <option key={idx} value={gsm}>{gsm}</option>
      ))}
    </select>

  </div>
)}
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
            <p>{abstract || "\n\n \t Abstract will appear here once ready.\n\n"}</p>
          </div>
          <div className="card-inner" style={{ flex: 1 }}>
            <div className="card-header">Abstract Predicates</div>
            <p>{abstractPredicates || "\n\n \t Abstract predicates will appear here once ready. \n\n"}</p>
            
            {abstractPredicates && (
                <button className="button" 
                onClick={() => generateMeTTaCode("abstract_predicates",abstractPredicates)}
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
            <p>{gseMetadataPredicates || "\n\n \t GSE metadata predicates will appear here once ready. \n\n"}</p>
            {gseMetadataPredicates && (
                <button className="button" 
                onClick={() => generateMeTTaCode("gse_metadata_predicates",gseMetadataPredicates)}
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

          {gsmTableData && (
  <div
    ref={tableRef}
    className="card"
    style={{ marginTop: '2rem', overflowX: 'auto' }}
  >
    <div className="card-header">GSM Data Table </div>
    <table className="gsm-table">
      <thead>
        <tr>
          {Object.keys(gsmTableData).map((col, idx) => (
            <th key={idx}>{col}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Object.values(gsmTableData[Object.keys(gsmTableData)[0]]).map((_, rowIndex) => (
          <tr key={rowIndex}>
            {Object.keys(gsmTableData).map((col, colIndex) => (
              <td key={colIndex}>{gsmTableData[col][rowIndex]}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>

    {gsmTableData && (
                <button className="button" 
                onClick={() => generateMeTTaCodeForGsm()}
                >
                  Generate MeTTa Code
                </button>
              )}

              {mettaCodeGSM && (
  <div className="card" style={{ marginTop: '1rem' }}>
    <div className="card-header">Generated MeTTa Code</div>
    <pre
      className="metta-code"
      onClick={() => {
        navigator.clipboard.writeText(mettaCodeGSM.join('\n'));
        alert('MeTTa code copied to clipboard!');
      }}
      title="Click to copy"
    >
      <code>{mettaCodeGSM.join('\n')}</code>
    </pre>
  </div>
)}


  </div>
)}

        </div>
      </div>
    </div>
  );
}

export default App;