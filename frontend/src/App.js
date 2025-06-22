// frontend/src/App.jsx
import './App.css'; 
import { useState, useEffect, useRef  } from 'react';
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
  
  const [gsmIds, setGsmIds] = useState([]);
  const [selectedGsmId, setSelectedGsmId] = useState('');
  const [gsmTableData, setGsmTableData] = useState('');
  const [mettaCodeGSM, setMettaCodeGSM] = useState([]);
  const [dropdownEnabled, setDropdownEnabled] = useState(false);
  const [copyMessage, setCopyMessage] = useState('');
  const tableRef = useRef(null);

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
    
    setAbstract('');
    setAbstractPredicates('');
    setGseMetadataPredicates('');
    setMettaCodeAbstract(null);
    setMettaCodeGSE(null);
    setGsmIds([]);
    setSelectedGsmId('');
    setGsmTableData('');
    setMettaCodeGSM([]);

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
      setCopyMessage('Error generating MeTTa code.');
      setTimeout(() => setCopyMessage(''), 3000);
    }
  };

  const fetchGsmTableData = async (gseId, gsmId) => {
    if (!gseId || !gsmId) {
      console.error("GSE ID or GSM ID is missing for fetching table data.");
      return;
    }
    setGsmTableData('');
    setMettaCodeGSM(null);
    setMessages((prev) => [...prev, `Fetching data for ${gsmId}...`]);
    try {
      const response = await fetch(`${backendUrl}/get_gsm?gse_id=${gseId}&gsm_id=${gsmId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch GSM data for ${gsmId}`);
      }

      const data = await response.json();
      setGsmTableData(JSON.stringify(data, null, 2) || `No data available for ${gsmId}.`);
      setMessages((prev) => [...prev, `Data for ${gsmId} fetched.`]);
    } catch (err) {
      console.error(`Error fetching GSM table data for ${gsmId}:`, err);
      setGsmTableData(`Error fetching data: ${err.message}`);
      setMessages((prev) => [...prev, `Failed to fetch data for ${gsmId}.`]);
    }
  };

  const generateMeTTaCodeForGsm = async () => {
    if (!gseId || !selectedGsmId) {
      setCopyMessage("Please select a GSE ID and a GSM ID first.");
      setTimeout(() => setCopyMessage(''), 3000);
      return;
    }
    setMessages((prev) => [...prev, `Generating MeTTa code for ${selectedGsmId}...`]);
    try {
      const response = await fetch(`${backendUrl}/gsm_to_metta?gse_id=${gseId}&gsm_id=${selectedGsmId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to generate MeTTa code for ${selectedGsmId}`);
      }

      const data = await response.json();
      const rawMeTTa = Array.isArray(data.table_metta)
        ? data.table_metta.join('\n')
        : data.table_metta.toString();

      setMettaCodeGSM(rawMeTTa || '');
      setMessages((prev) => [...prev, `MeTTa code for ${selectedGsmId} generated.`]);
    } catch (err) {
      console.error(`Error generating MeTTa code for GSM ${selectedGsmId}:`, err);
      setCopyMessage('Error generating MeTTa code for GSM.');
      setTimeout(() => setCopyMessage(''), 3000);
      setMettaCodeGSM(`Error generating MeTTa code: ${err.message}`);
      setMessages((prev) => [...prev, `Failed to generate MeTTa code for ${selectedGsmId}.`]);
    }
  };

  useEffect(() => {
    const ws = new WebSocket(`${backendWsUrl}/ws/${clientId}`);

    

  ws.onmessage = (event) => {
    const message = event.data;

      try {
        const json = JSON.parse(message);

        if (json.abstract) {
          setAbstract(json.abstract);
        }

        if (json.abstract_predicates) {
          setAbstractPredicates(json.abstract_predicates);
        }

        if (json.gsms && Array.isArray(json.gsms.gsm_ids)) {
          setGsmIds(json.gsms.gsm_ids);
          setDropdownEnabled(true);
        }

        if (json.gsm_ids && Array.isArray(json.gsm_ids)) {
          setGsmIds(json.gsm_ids);
        }

        if (!json.abstract && !json.abstract_predicates && !json.gse_metadata_predicates && !json.gsm_ids) {
          setMessages((prev) => [...prev, message]);
        }

    } catch {
      // Not JSON, treat as progress update
      setMessages((prev) => [...prev, message]);
    }
  };

  return () => ws.close();
}, [clientId]);
    

    useEffect(() => {
      if (gsmTableData && tableRef.current) {
        tableRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }, [gsmTableData]);



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

          <div style={{ marginTop: '1.5rem' }}>
            <p className="description" style={{ marginBottom: '0.5rem' }}>Choose GSM ID for further info:</p>
            <select
              className="input"
              value={selectedGsmId}
              onChange={(e) => {
                setSelectedGsmId(e.target.value);
                if (e.target.value) {
                  fetchGsmTableData(gseId, e.target.value);
                } else {
                  setGsmTableData('');
                  setMettaCodeGSM([]);
                }
              }}
              disabled={loading || gsmIds.length === 0}
            >
              <option value="">-- Please choose a GSM ID --</option>
              {gsmIds.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
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
                width: `${Math.min((messages.length / 8) * 100, 100)}%`,
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

          <div className="card-inner" style={{ flex: 1 }} ref={tableRef}>
            <div className="card-header">GSM Table: {selectedGsmId || "No GSM Selected"}</div>

            <p>{gsmTableData || "\n\n \t GSM table data will appear here once a GSM is selected.\n\n"}</p>
            {selectedGsmId && gsmTableData && (
              <button
                className="button"
                onClick={generateMeTTaCodeForGsm}
              >
                Generate GSM MeTTa Code
              </button>
            )}
          </div>

          <div className="card-inner" style={{ flex: 1 }}>
            <div className="card-header">GSM MeTTa Code</div>
            <pre className="metta-code"
              onClick={() => {
                navigator.clipboard.writeText(mettaCodeGSM || '');
                setCopyMessage('GSM MeTTa code copied to clipboard!');
                setTimeout(() => setCopyMessage(''), 3000);
              }}
              title="Click to copy"
            >
              <code>{mettaCodeGSM.join('\n GSM MeTTa code will appear here once generated.')}</code>

            </pre>
          </div>
        </div>
      </div>
      {copyMessage && (
        <div className="copy-message-box">
          {copyMessage}
        </div>
      )}
      </div>
    </div>
  );
}

export default App;