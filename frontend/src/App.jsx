import './App.css';
import { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { parseGsmTable } from './gsmTable';

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
  const [gsmLoading, setGsmLoading] = useState(false);
  const [gsmError, setGsmError] = useState('');
  const gsmRequestId = useRef(0);
  const tableRef = useRef(null);
  const hasGsmRows = (gsmTableData?.rowKeys.length ?? 0) > 0;


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
      const abstractContent = predicates
      const response = await fetch(`${backendUrl}/convert_fol_to_metta`, {
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
          gsmRequestId.current += 1;
          setGsmTableData(null);
          setMettaCodeGSM(null);
          setGsmLoading(false);
          setGsmError('');
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

    return () => {
      gsmRequestId.current += 1;
      ws.close();
    };
  }, [clientId]);

  // The handler for GSM selection
  const fetchGsmData = async (gsmId) => {
    const requestId = ++gsmRequestId.current;
    setGsmTableData(null);
    setMettaCodeGSM(null);
    setGsmError('');
    setGsmLoading(true);
    try {
      const response = await fetch(`${backendUrl}/get_gsm?gse_id=${gseId}&gsm_id=${gsmId}`, {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'text/plain',
        },
      });

      if (!response.ok) throw new Error(`Failed to fetch GSM data (HTTP ${response.status}).`);

      const data = await response.json();

      if (requestId !== gsmRequestId.current) return;
      setGsmTableData(parseGsmTable(data));

      setTimeout(() => {
        if (requestId === gsmRequestId.current && tableRef.current) {
          tableRef.current.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);

    } catch (error) {
      if (requestId === gsmRequestId.current) {
        setGsmError(`Unable to load GSM table: ${error?.message || 'Please try again.'}`);
      }
    } finally {
      if (requestId === gsmRequestId.current) setGsmLoading(false);
    }
  };

  const generateMeTTaCodeForGsm = async () => {
    if (!hasGsmRows || gsmLoading) return;
    const requestId = gsmRequestId.current;
    try {
      const gsmId = selectedGsm;
      const response = await fetch(`${backendUrl}/gsm_to_metta?gse_id=${gseId}&gsm_id=${gsmId}`, {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'text/plain',
        },
      });

      if (!response.ok) throw new Error('Failed to fetch GSM data');

      const gsmMetta = await response.json();
      if (requestId !== gsmRequestId.current) return;
      setMettaCodeGSM(gsmMetta.table_metta || []);

    }
    catch (error) {
      if (requestId !== gsmRequestId.current) return;
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
              aria-label="Select GSM"
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
                onClick={() => generateMeTTaCode("abstract_predicates", abstractPredicates)}
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
                onClick={() => generateMeTTaCode("gse_metadata_predicates", gseMetadataPredicates)}
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

          {selectedGsm && (
            <div
              ref={tableRef}
              className="card"
              style={{ marginTop: '2rem', overflowX: 'auto' }}
            >
              <div className="card-header">GSM Data Table </div>
              {gsmLoading ? (
                <p role="status">Loading GSM table...</p>
              ) : gsmError ? (
                <div role="alert" className="error-message">{gsmError}</div>
              ) : !hasGsmRows ? (
                <p role="status">No table data available for this GSM</p>
              ) : (
                <>
                  <table className="gsm-table">
                    <thead>
                      <tr>
                        {gsmTableData.columns.map((col) => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {gsmTableData.rowKeys.map((rowKey) => (
                        <tr key={rowKey}>
                          {gsmTableData.columns.map((col) => (
                            <td key={col}>{String(gsmTableData.data[col][rowKey] ?? '')}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  <button className="button"
                    onClick={() => generateMeTTaCodeForGsm()}
                  >
                    Generate MeTTa Code
                  </button>

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
                </>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default App;
