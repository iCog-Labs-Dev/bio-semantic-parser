import './App.css';
import { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { parseGsmTable } from './gsmTable';
import { explainError, requestJson } from './api';

const backendUrl = process.env.REACT_APP_BACKEND_URL;
const backendWsUrl = process.env.REACT_APP_BACKEND_WS_URL;
const configured = Boolean(backendUrl && backendWsUrl);
const post = { method: 'POST' };
const textFromPredicates = (value) => {
  if (typeof value === 'string') return value;
  if (Array.isArray(value) && value.every((item) => typeof item === 'string')) return value.join('\n');
  throw new Error('Unexpected predicate response.');
};

function ErrorNotice({ title, error, onRetry, retryLabel = 'Try again' }) {
  if (!error) return null;
  return (
    <div className="error-notice" role="alert">
      <strong>{title}</strong>
      <div className="notice-description">{explainError(error)}</div>
      {onRetry && <button className="secondary-button" onClick={onRetry}>{retryLabel}</button>}
      <details>
        <summary>Technical details</summary>
        <pre>{error.details || error.message}</pre>
      </details>
    </div>
  );
}

function CodeBlock({ code }) {
  const [copyStatus, setCopyStatus] = useState('');
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopyStatus('Copied to clipboard.');
    } catch {
      setCopyStatus('Copy isn’t available here. Select the code and copy it manually.');
    }
  };
  return (
    <div className="code-output">
      <div className="code-toolbar">
        <span>Generated MeTTa</span>
        <button className="secondary-button" onClick={copy}>Copy code</button>
      </div>
      <pre className="metta-code"><code>{code}</code></pre>
      <div className="copy-status" role="status">{copyStatus}</div>
    </div>
  );
}

function MettaConversion({ endpoint, body, field = 'metta_valid' }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [code, setCode] = useState(null);
  const requestId = useRef(0);
  useEffect(() => () => { requestId.current += 1; }, []);

  const generate = async () => {
    if (loading) return;
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const data = await requestJson(`${backendUrl}/${endpoint}`, {
        ...post, headers: { 'Content-Type': 'text/plain' },
        ...(body !== undefined ? { body } : {}),
      });
      const output = textFromPredicates(data?.[field]);
      if (id === requestId.current) setCode(output);
    } catch (err) {
      if (id === requestId.current) setError(err);
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  };
  return (
    <div className="conversion" aria-busy={loading}>
      <button className="button" onClick={generate} disabled={loading}>
        {loading ? 'Generating MeTTa…' : 'Generate MeTTa Code'}
      </button>
      <ErrorNotice title="Couldn’t generate MeTTa" error={error} onRetry={generate} />
      {code !== null && (code ? <CodeBlock key={code} code={code} /> : <div className="empty-state" role="status">No MeTTa expressions were returned.</div>)}
    </div>
  );
}

function App() {
  const [clientId] = useState(uuidv4);
  const [connection, setConnection] = useState(configured ? 'connecting' : 'unconfigured');
  const [connectionAttempt, setConnectionAttempt] = useState(0);
  const [phase, setPhase] = useState('idle');
  const [progress, setProgress] = useState('');
  const [abstract, setAbstract] = useState('');
  const [abstractPredicates, setAbstractPredicates] = useState('');
  const [gseMetadataPredicates, setGseMetadataPredicates] = useState('');
  const [gseId, setGseId] = useState('');
  const [studyId, setStudyId] = useState('');
  const [studyVersion, setStudyVersion] = useState(0);
  const [validationError, setValidationError] = useState('');
  const [processError, setProcessError] = useState(null);
  const [gsmList, setGsmList] = useState([]);
  const [selectedGsm, setSelectedGsm] = useState('');
  const [gsmTableData, setGsmTableData] = useState(null);
  const [gsmLoading, setGsmLoading] = useState(false);
  const [gsmError, setGsmError] = useState(null);
  const gsmRequestId = useRef(0);
  const processing = useRef(false);
  const completed = useRef(false);
  const updatesInterrupted = useRef(false);
  const mounted = useRef(false);
  const tableRef = useRef(null);
  const loading = phase === 'running';
  const hasGsmRows = (gsmTableData?.rowKeys.length ?? 0) > 0;
  const isValidGseId = (id) => /^GSE\d+$/.test(id);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; gsmRequestId.current += 1; };
  }, []);

  useEffect(() => {
    if (selectedGsm) tableRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [selectedGsm]);

  useEffect(() => {
    if (!configured) return;
    let disposed = false;
    let ws;
    const disconnected = () => {
      if (!disposed) {
        if (processing.current) updatesInterrupted.current = true;
        setConnection('disconnected');
      }
    };
    setConnection('connecting');
    try {
      ws = new WebSocket(`${backendWsUrl}/ws/${clientId}`);
      ws.onopen = () => { if (!disposed) setConnection('connected'); };
      ws.onerror = disconnected;
      ws.onclose = disconnected;
      ws.onmessage = (event) => {
        if (disposed) return;
        try {
          const json = JSON.parse(event.data);
          if (!json || typeof json !== 'object' || Array.isArray(json)) throw new Error('Unexpected progress response.');
          if (json.error) throw new Error(typeof json.error === 'string' ? json.error : 'The server reported a processing error.');
          if (json.gsms) {
            if (typeof json.gsms.gse_id !== 'string' || !/^GSE\d+$/.test(json.gsms.gse_id)
              || !Array.isArray(json.gsms.gsm_ids) || !json.gsms.gsm_ids.every((id) => typeof id === 'string')) {
              throw new Error('Unexpected sample list response.');
            }
            setStudyId(json.gsms.gse_id);
            setGsmList(json.gsms.gsm_ids);
            setSelectedGsm('');
            gsmRequestId.current += 1;
            setGsmTableData(null);
            setGsmLoading(false);
            setGsmError(null);
          }
          if (json.abstract !== undefined) setAbstract(textFromPredicates(json.abstract));
          if (json.abstract_predicates !== undefined) setAbstractPredicates(textFromPredicates(json.abstract_predicates));
          if (json.gse_metadata_predicates !== undefined) setGseMetadataPredicates(textFromPredicates(json.gse_metadata_predicates));
        } catch (err) {
          // The API also sends plain-text progress messages over this connection.
          const text = event.data.trim();
          if (err instanceof SyntaxError && !text.startsWith('{') && !text.startsWith('[')) {
            if (/^done\b/i.test(event.data.trim())) {
              completed.current = true;
              if (!processing.current && !updatesInterrupted.current) {
                setPhase((previous) => previous === 'incomplete' ? 'complete' : previous);
              }
            } else if (/^(error|failed)\b/i.test(event.data.trim())) {
              setProcessError(new Error(event.data));
            } else {
              setProgress(event.data);
            }
          } else {
            setProcessError(err);
          }
        }
      };
    } catch {
      disconnected();
    }
    return () => { disposed = true; ws?.close(); };
  }, [clientId, connectionAttempt]);

  const startProcess = async (requestedStudy = gseId) => {
    if (processing.current || connection !== 'connected' || !isValidGseId(requestedStudy)) return;
    processing.current = true;
    completed.current = false;
    updatesInterrupted.current = false;
    setPhase('running');
    setProcessError(null);
    setProgress('Starting the extraction…');
    setStudyId(requestedStudy);
    setStudyVersion((version) => version + 1);
    setAbstract('');
    setAbstractPredicates('');
    setGseMetadataPredicates('');
    setGsmList([]);
    setSelectedGsm('');
    gsmRequestId.current += 1;
    setGsmTableData(null);
    setGsmLoading(false);
    setGsmError(null);
    try {
      const data = await requestJson(`${backendUrl}/process?client_id=${clientId}&gse_id=${requestedStudy}`, post);
      if (data?.status !== 'ok') throw new Error('Unexpected processing response.');
      if (mounted.current) setPhase(completed.current && !updatesInterrupted.current ? 'complete' : 'incomplete');
    } catch (err) {
      if (mounted.current) { setProcessError(err); setPhase('failed'); }
    } finally {
      processing.current = false;
    }
  };

  const fetchGsmData = async (gsmId) => {
    const requestId = ++gsmRequestId.current;
    setGsmTableData(null);
    setGsmError(null);
    setGsmLoading(true);
    try {
      const data = await requestJson(`${backendUrl}/get_gsm?gse_id=${studyId}&gsm_id=${gsmId}`, post);
      if (requestId !== gsmRequestId.current) return;
      setGsmTableData(parseGsmTable(data));
    } catch (err) {
      if (requestId === gsmRequestId.current) setGsmError(err);
    } finally {
      if (requestId === gsmRequestId.current) setGsmLoading(false);
    }
  };

  const status = processError ? 'Extraction interrupted' : {
    idle: 'Ready to start', running: progress, complete: 'Extraction complete',
    failed: 'Extraction interrupted', incomplete: 'Extraction results may be incomplete',
  }[phase];

  return (
    <div className="app">
      <aside className="sidebar">
        <h1 className="title">Semantic Parser</h1>
        <p className="description">Extract biomedical predicates from a GEO study.</p>
        <label className="input-label" htmlFor="gse-id">GEO Series ID</label>
        <input className="input" id="gse-id" name="gseId" type="text" placeholder="e.g., GSE12345"
          value={gseId} aria-invalid={Boolean(validationError)} aria-describedby={validationError ? 'gse-validation' : undefined}
          onChange={(e) => {
            const value = e.target.value.trim().toUpperCase();
            setGseId(value);
            setValidationError(value && !/^G(S(E\d*)?)?$/.test(value) ? 'Use GSE followed by digits, for example GSE12345.' : '');
          }}
          onKeyDown={(e) => { if (e.key === 'Enter') startProcess(); }} disabled={loading} />
        {validationError && <div id="gse-validation" className="error-message">{validationError}</div>}
        <button className="button" id="fetch-btn" onClick={() => startProcess()}
          disabled={loading || !isValidGseId(gseId) || connection !== 'connected'}>
          {loading ? <><span className="spinner" />Parsing…</> : 'Parse'}
        </button>
        <div className="connection-status" role="status">
          {connection === 'connected' ? 'Connected to server' : connection === 'connecting' ? 'Connecting to server…' : 'Server connection unavailable'}
        </div>
        {gsmList.length > 0 && (
          <div className="sample-picker">
            <label className="input-label" htmlFor="gsm-select">Select GSM</label>
            <select id="gsm-select" className="input" value={selectedGsm} onChange={(e) => {
              setSelectedGsm(e.target.value); fetchGsmData(e.target.value);
            }}>
              <option value="" disabled>Select a GSM ID</option>
              {gsmList.map((gsm) => <option key={gsm} value={gsm}>{gsm}</option>)}
            </select>
          </div>
        )}
      </aside>

      <main className="main">
        {!configured && <div className="error-notice" role="alert">
          <strong>Server connection isn’t configured</strong>
          <div className="notice-description">Ask the deployment owner to set the backend HTTP and WebSocket URLs, then restart the interface.</div>
        </div>}
        {connection === 'disconnected' && <div className="error-notice" role="alert">
          <strong>Progress connection lost</strong>
          <div className="notice-description">Live updates are unavailable. Reconnect before starting another extraction.
            {loading && ' The current request may still be running; reconnecting won’t restart it or recover missed results.'}</div>
          <button className="secondary-button" onClick={() => setConnectionAttempt((attempt) => attempt + 1)}>Reconnect</button>
        </div>}
        <section className="card">
          <div className="card-header">Extraction {studyId && <span className="study-label">{studyId}</span>}</div>
          <div className="status-bar" role="status">{status}</div>
          {loading && !processError && <div className="activity-bar" aria-label="Extraction in progress" />}
          <ErrorNotice title="Couldn’t finish the extraction" error={processError}
            onRetry={!loading && connection === 'connected' && isValidGseId(studyId) ? () => {
              setGseId(studyId); setValidationError(''); startProcess(studyId);
            } : undefined} retryLabel="Retry extraction" />
          {phase === 'incomplete' && !processError && <div className="empty-state" role="status">
            The server finished, but this page didn’t receive a complete set of updates. Any results received are shown below.
            Reconnect if needed, then retry or try another study.
          </div>}
          <section className="card-inner">
            <h2 className="card-header">Abstract</h2>
            {abstract ? <p className="abstract-text">{abstract}</p> : <div className="empty-state">The linked abstract will appear here.</div>}
          </section>
          <section className="card-inner">
            <h2 className="card-header">Abstract Predicates</h2>
            {abstractPredicates ? <>
              <p className="predicate-text">{abstractPredicates}</p>
              <MettaConversion key={`abstract-${studyVersion}`} endpoint="convert_fol_to_metta" body={abstractPredicates} />
            </> : <div className="empty-state">Extracted abstract predicates will appear here.</div>}
          </section>
          <section className="card-inner">
            <h2 className="card-header">GSE Metadata Predicates</h2>
            {gseMetadataPredicates ? <>
              <p className="predicate-text">{gseMetadataPredicates}</p>
              <MettaConversion key={`metadata-${studyVersion}`} endpoint="convert_fol_to_metta" body={gseMetadataPredicates} />
            </> : <div className="empty-state">Extracted study predicates will appear here.</div>}
          </section>
          {selectedGsm && <section ref={tableRef} className="card-inner">
            <h2 className="card-header">GSM Data Table <span className="study-label">{selectedGsm}</span></h2>
            {gsmLoading ? <div className="empty-state" role="status">Loading GSM table...</div>
              : gsmError ? <ErrorNotice title="Couldn’t load this sample" error={gsmError} onRetry={() => fetchGsmData(selectedGsm)} />
              : !hasGsmRows ? <div className="empty-state" role="status">
                <div>No table data available for this GSM</div>
                <div>You can select another sample. The study results remain available above.</div>
              </div>
              : <>
                <div className="table-scroll"><table className="gsm-table">
                  <thead><tr>{gsmTableData.columns.map((col) => <th key={col} scope="col">{col}</th>)}</tr></thead>
                  <tbody>{gsmTableData.rowKeys.map((rowKey) => <tr key={rowKey}>
                    {gsmTableData.columns.map((col) => <td key={col}>{String(gsmTableData.data[col][rowKey] ?? '')}</td>)}
                  </tr>)}</tbody>
                </table></div>
                <MettaConversion key={`${studyVersion}-${selectedGsm}`} endpoint={`gsm_to_metta?gse_id=${studyId}&gsm_id=${selectedGsm}`} field="table_metta" />
              </>}
          </section>}
        </section>
      </main>
    </div>
  );
}

export default App;
