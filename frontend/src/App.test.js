import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';

process.env.REACT_APP_BACKEND_URL = 'http://backend.test:8010';
process.env.REACT_APP_BACKEND_WS_URL = 'ws://backend.test:8010';
const App = require('./App').default;

let socket;
const originalFetch = global.fetch;
const originalWebSocket = global.WebSocket;
const originalScrollIntoView = HTMLElement.prototype.scrollIntoView;

const response = (data) => ({ ok: true, status: 200, json: async () => data });
const populatedTable = { ID_REF: { 0: 'probe-a', 1: 'probe-b' }, VALUE: { 0: 1.5, 1: null } };

function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}

function showGsmChoices() {
  render(<App />);
  fireEvent.change(screen.getByPlaceholderText('e.g., GSE12345'), {
    target: { value: 'GSE12345' },
  });
  act(() => {
    socket.onmessage({
      data: JSON.stringify({ gsms: { gse_id: 'GSE12345', gsm_ids: ['GSM1', 'GSM2'] } }),
    });
  });
}

function selectGsm(gsmId = 'GSM1') {
  fireEvent.change(screen.getByRole('combobox', { name: 'Select GSM' }), {
    target: { value: gsmId },
  });
}

beforeEach(() => {
  global.fetch = jest.fn();
  global.WebSocket = jest.fn(function () {
    socket = this;
    this.close = jest.fn();
  });
  HTMLElement.prototype.scrollIntoView = jest.fn();
  jest.spyOn(console, 'log').mockImplementation(() => {});
});

afterEach(() => {
  global.fetch = originalFetch;
  global.WebSocket = originalWebSocket;
  HTMLElement.prototype.scrollIntoView = originalScrollIntoView;
  jest.restoreAllMocks();
});

test.each([
  ['no columns', {}],
  ['columns without rows', { ID_REF: {}, VALUE: {} }],
])('keeps the app usable for a GSM table with %s', async (_, data) => {
  global.fetch.mockResolvedValueOnce(response(data));
  showGsmChoices();
  selectGsm();

  expect(await screen.findByText('No table data available for this GSM')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'Semantic Parser' })).toBeInTheDocument();
  expect(screen.getByRole('combobox', { name: 'Select GSM' })).toBeEnabled();
  expect(screen.queryByRole('table')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Generate MeTTa Code' })).not.toBeInTheDocument();
});

test('renders populated columns and blank cells for null values', async () => {
  global.fetch.mockResolvedValueOnce(response(populatedTable));
  showGsmChoices();
  selectGsm();

  const rows = within(await screen.findByRole('table')).getAllByRole('row');
  expect(within(rows[0]).getAllByRole('columnheader').map((cell) => cell.textContent)).toEqual(['ID_REF', 'VALUE']);
  expect(within(rows[1]).getAllByRole('cell').map((cell) => cell.textContent)).toEqual(['probe-a', '1.5']);
  expect(within(rows[2]).getAllByRole('cell').map((cell) => cell.textContent)).toEqual(['probe-b', '']);
  expect(screen.getByRole('button', { name: 'Generate MeTTa Code' })).toBeEnabled();
});

test('uses actual row keys when indexes are nonsequential', async () => {
  global.fetch.mockResolvedValueOnce(response({
    ID_REF: { 10: 'probe-ten', 42: 'probe-forty-two' },
    VALUE: { 10: 0, 42: false },
  }));
  showGsmChoices();
  selectGsm();

  const rows = within(await screen.findByRole('table')).getAllByRole('row');
  expect(within(rows[1]).getAllByRole('cell').map((cell) => cell.textContent)).toEqual(['probe-ten', '0']);
  expect(within(rows[2]).getAllByRole('cell').map((cell) => cell.textContent)).toEqual(['probe-forty-two', 'false']);
});

test.each([
  ['null', null],
  ['an array', []],
  ['a primitive', 'unexpected'],
  ['a null column', { ID_REF: null }],
  ['an array column', { ID_REF: [] }],
  ['an error object', { error: 'Sample not found' }],
  ['an object cell', { ID_REF: { 0: { unexpected: true } } }],
  ['an array cell', { ID_REF: { 0: [] } }],
  ['mismatched row keys', { ID_REF: { 10: 'probe' }, VALUE: { 11: 2 } }],
  ['mismatched row counts', { ID_REF: {}, VALUE: { 10: 2 } }],
])('shows an inline error instead of crashing for %s', async (_, data) => {
  global.fetch.mockResolvedValueOnce(response(data));
  showGsmChoices();
  selectGsm();

  expect(await screen.findByRole('alert')).toHaveTextContent('Invalid GSM table response.');
  expect(screen.getByRole('heading', { name: 'Semantic Parser' })).toBeInTheDocument();
  expect(screen.queryByRole('table')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Generate MeTTa Code' })).not.toBeInTheDocument();
});

test('shows an inline error when fetching a sample fails', async () => {
  global.fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));
  showGsmChoices();
  selectGsm();
  expect(await screen.findByRole('alert')).toHaveTextContent('We couldn’t reach the server.');
  expect(screen.getByRole('button', { name: 'Try again' })).toBeEnabled();
});

test('shows an inline error for an unsuccessful HTTP response', async () => {
  global.fetch.mockResolvedValueOnce({ ok: false, status: 500 });
  showGsmChoices();
  selectGsm();
  expect(await screen.findByRole('alert')).toHaveTextContent('HTTP 500');
});

test('clears the old table and generated MeTTa while loading another sample', async () => {
  global.fetch.mockResolvedValueOnce(response(populatedTable));
  showGsmChoices();
  selectGsm();
  await screen.findByRole('table');

  global.fetch.mockResolvedValueOnce(response({ table_metta: ['(value sample-one 1.5)'] }));
  fireEvent.click(screen.getByRole('button', { name: 'Generate MeTTa Code' }));
  await screen.findByText('(value sample-one 1.5)');

  const pending = deferred();
  global.fetch.mockReturnValueOnce(pending.promise);
  selectGsm('GSM2');
  expect(screen.queryByRole('table')).not.toBeInTheDocument();
  expect(screen.queryByText('(value sample-one 1.5)')).not.toBeInTheDocument();
  expect(screen.getByText('Loading GSM table...')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Generate MeTTa Code' })).not.toBeInTheDocument();

  await act(async () => pending.resolve(response({})));
  expect(await screen.findByText('No table data available for this GSM')).toBeInTheDocument();
});

test('ignores a previous sample response that arrives after the new selection', async () => {
  const previous = deferred();
  global.fetch.mockReturnValueOnce(previous.promise);
  showGsmChoices();
  selectGsm();

  global.fetch.mockResolvedValueOnce(response({ ID_REF: { 9: 'current-sample' } }));
  selectGsm('GSM2');
  await screen.findByText('current-sample');

  await act(async () => previous.resolve(response(populatedTable)));
  expect(screen.getByText('current-sample')).toBeInTheDocument();
  expect(screen.queryByText('probe-a')).not.toBeInTheDocument();
});

test('does not display late MeTTa output under another sample', async () => {
  global.fetch.mockResolvedValueOnce(response(populatedTable));
  showGsmChoices();
  selectGsm();
  await screen.findByRole('table');

  const previous = deferred();
  global.fetch.mockReturnValueOnce(previous.promise);
  fireEvent.click(screen.getByRole('button', { name: 'Generate MeTTa Code' }));

  global.fetch.mockResolvedValueOnce(response({ ID_REF: { 9: 'current-sample' } }));
  selectGsm('GSM2');
  await screen.findByText('current-sample');

  await act(async () => previous.resolve(response({ table_metta: ['(value previous-sample 1.5)'] })));
  expect(screen.queryByText('(value previous-sample 1.5)')).not.toBeInTheDocument();
});

test('clears a previous error when selecting a valid sample', async () => {
  global.fetch.mockResolvedValueOnce(response(null));
  showGsmChoices();
  selectGsm();
  await screen.findByRole('alert');

  global.fetch.mockResolvedValueOnce(response(populatedTable));
  selectGsm('GSM2');
  await screen.findByRole('table');
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

function prepareStudy() {
  render(<App />);
  fireEvent.change(screen.getByLabelText('GEO Series ID'), { target: { value: 'GSE12345' } });
  act(() => socket.onopen());
}

function send(data) {
  act(() => socket.onmessage({ data: typeof data === 'string' ? data : JSON.stringify(data) }));
}

test('recovers from an unreachable server without a runtime overlay or a stuck loading button', async () => {
  global.fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));
  prepareStudy();
  fireEvent.click(screen.getByRole('button', { name: 'Parse' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Couldn’t finish the extraction');
  expect(screen.getByRole('button', { name: 'Parse' })).toBeEnabled();

  const pending = deferred();
  global.fetch.mockReturnValueOnce(pending.promise);
  fireEvent.change(screen.getByLabelText('GEO Series ID'), { target: { value: 'GSE99999' } });
  fireEvent.click(screen.getByRole('button', { name: 'Retry extraction' }));
  expect(global.fetch.mock.calls[1][0]).toContain('gse_id=GSE12345');
  expect(screen.getByLabelText('GEO Series ID')).toHaveValue('GSE12345');
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  send('Fetching GSE data...');
  send('Done ');
  await act(async () => pending.resolve(response({ status: 'ok' })));
  expect(screen.getByText('Extraction complete')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Parse' })).toBeEnabled();
});

test('keeps diagnostics collapsed and retains partial results when the server fails', async () => {
  const pending = deferred();
  global.fetch.mockReturnValueOnce(pending.promise);
  prepareStudy();
  fireEvent.click(screen.getByRole('button', { name: 'Parse' }));
  send({ abstract: 'A partially retrieved abstract.' });
  await act(async () => pending.resolve({ ok: false, status: 500, text: async () => 'MedCAT internal traceback' }));
  const notice = await screen.findByRole('alert');
  expect(notice).toHaveTextContent('The server couldn’t complete this request.');
  expect(notice.querySelector('details')).not.toHaveAttribute('open');
  expect(within(notice).getByText(/MedCAT internal traceback/)).not.toBeVisible();
  expect(screen.getByText('A partially retrieved abstract.')).toBeInTheDocument();

  global.fetch.mockReturnValueOnce(new Promise(() => {}));
  fireEvent.click(screen.getByRole('button', { name: 'Retry extraction' }));
  expect(screen.queryByText('A partially retrieved abstract.')).not.toBeInTheDocument();
});

test('does not report success when the API returns ok without a completion message', async () => {
  global.fetch.mockResolvedValueOnce(response({ status: 'ok' }));
  prepareStudy();
  fireEvent.click(screen.getByRole('button', { name: 'Parse' }));
  expect(await screen.findByText(/The server finished, but this page didn’t receive/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Parse' })).toBeEnabled();
  send('Done ');
  expect(screen.getByText('Extraction complete')).toBeInTheDocument();
});

test.each([
  ['unreadable JSON', { ok: true, json: async () => { throw new SyntaxError('Unexpected token'); } }],
  ['unexpected content', response({ unexpected: true })],
])('handles %s from the process request', async (_, data) => {
  global.fetch.mockResolvedValueOnce(data);
  prepareStudy();
  fireEvent.click(screen.getByRole('button', { name: 'Parse' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Couldn’t finish the extraction');
  expect(screen.getByRole('button', { name: 'Parse' })).toBeEnabled();
});

test('allows reconnecting after a WebSocket failure and ignores the previous socket', () => {
  render(<App />);
  fireEvent.change(screen.getByLabelText('GEO Series ID'), { target: { value: 'GSE12345' } });
  expect(screen.getByRole('button', { name: 'Parse' })).toBeDisabled();
  const previous = socket;
  act(() => socket.onerror());
  expect(screen.getByRole('alert')).toHaveTextContent('Progress connection lost');
  fireEvent.click(screen.getByRole('button', { name: 'Reconnect' }));
  expect(previous.close).toHaveBeenCalled();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  act(() => socket.onopen());
  act(() => previous.onclose());
  expect(screen.getByRole('button', { name: 'Parse' })).toBeEnabled();
  expect(global.fetch).not.toHaveBeenCalled();
});

test('does not restart an in-flight extraction when reconnecting', async () => {
  const pending = deferred();
  global.fetch.mockReturnValueOnce(pending.promise);
  prepareStudy();
  fireEvent.click(screen.getByRole('button', { name: 'Parse' }));
  act(() => socket.onclose());
  expect(screen.getByRole('alert')).toHaveTextContent('The current request may still be running');
  fireEvent.click(screen.getByRole('button', { name: 'Reconnect' }));
  act(() => socket.onopen());
  expect(screen.getByRole('button', { name: 'Parsing…' })).toBeDisabled();
  expect(global.fetch).toHaveBeenCalledTimes(1);
  send('Done ');
  await act(async () => pending.resolve(response({ status: 'ok' })));
  expect(screen.getByRole('button', { name: 'Parse' })).toBeEnabled();
  expect(screen.queryByText('Extraction complete')).not.toBeInTheDocument();
  expect(screen.getByText('Extraction results may be incomplete')).toBeInTheDocument();
});

test.each([
  { gsms: { gsm_ids: null } },
  { gsms: { gse_id: { unexpected: 'object' }, gsm_ids: ['GSM1'] } },
  { abstract_predicates: { unexpected: 'object' } },
  { error: 'Model unavailable' },
  '{bad JSON',
  'Error: model unavailable',
])('handles malformed progress or a server error without rendering a broken page: %j', (data) => {
  prepareStudy();
  send(data);
  expect(screen.getByRole('alert')).toHaveTextContent('Couldn’t finish the extraction');
  expect(screen.getByRole('heading', { name: 'Semantic Parser' })).toBeInTheDocument();
});

test('does not display sample-list JSON as a progress update', () => {
  showGsmChoices();
  expect(screen.queryByText(/"gsm_ids"/)).not.toBeInTheDocument();
});

test('labels sampled demo results and clears the label on a new extraction', () => {
  prepareStudy();
  send({ demo: { metadata_samples: 2, abstract_chunks: 2 } });
  expect(screen.getByText(/Demo mode: up to 2 GSM metadata records and 2 abstract chunks/)).toBeInTheDocument();
  global.fetch.mockReturnValueOnce(new Promise(() => {}));
  fireEvent.click(screen.getByRole('button', { name: 'Parse' }));
  expect(screen.queryByText(/Demo mode:/)).not.toBeInTheDocument();
});

test('retries a failed sample without changing the selected sample', async () => {
  global.fetch.mockResolvedValueOnce({ ok: false, status: 503 });
  showGsmChoices();
  selectGsm();
  await screen.findByRole('alert');
  expect(HTMLElement.prototype.scrollIntoView).toHaveBeenCalled();
  global.fetch.mockResolvedValueOnce(response(populatedTable));
  fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
  await screen.findByRole('table');
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByRole('combobox')).toHaveValue('GSM1');
});

test.each([
  [404, 'The requested resource wasn’t found.'],
  [429, 'The service is receiving too many requests.'],
  [401, 'The server denied this request.'],
  [403, 'The server denied this request.'],
])('gives actionable guidance for HTTP %s', async (status, message) => {
  global.fetch.mockResolvedValueOnce({ ok: false, status });
  showGsmChoices();
  selectGsm();
  expect(await screen.findByRole('alert')).toHaveTextContent(message);
});

test('keeps MeTTa errors next to the sample and recovers on retry', async () => {
  const alert = jest.spyOn(window, 'alert').mockImplementation(() => {});
  global.fetch.mockResolvedValueOnce(response(populatedTable));
  showGsmChoices();
  selectGsm();
  await screen.findByRole('table');
  global.fetch.mockResolvedValueOnce({ ok: false, status: 500 });
  fireEvent.click(screen.getByRole('button', { name: 'Generate MeTTa Code' }));
  const notice = await screen.findByRole('alert');
  expect(notice).toHaveTextContent('Couldn’t generate MeTTa');
  expect(screen.getByRole('table')).toBeInTheDocument();
  expect(alert).not.toHaveBeenCalled();

  const pending = deferred();
  global.fetch.mockReturnValueOnce(pending.promise);
  fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
  expect(screen.getByRole('button', { name: 'Generating MeTTa…' })).toBeDisabled();
  await act(async () => pending.resolve(response({ table_metta: ['(value a 1)', '(value b 2)'] })));
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByText(/\(value a 1\)/)).toHaveTextContent('(value a 1) (value b 2)');
});

test('normalizes predicate arrays for display and conversion, and handles malformed conversion results', async () => {
  prepareStudy();
  send({ abstract_predicates: ['Gene(A)', 'Gene(B)'] });
  global.fetch.mockResolvedValueOnce(response({ metta_valid: null }));
  fireEvent.click(screen.getByRole('button', { name: 'Generate MeTTa Code' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Couldn’t generate MeTTa');
  expect(global.fetch.mock.calls[0][1].body).toBe('Gene(A)\nGene(B)');
});

test('offers manual copying when the clipboard is unavailable', async () => {
  const alert = jest.spyOn(window, 'alert').mockImplementation(() => {});
  prepareStudy();
  send({ abstract_predicates: ['Gene(A)'] });
  global.fetch.mockResolvedValueOnce(response({ metta_valid: ['(Gene A)'] }));
  fireEvent.click(screen.getByRole('button', { name: 'Generate MeTTa Code' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Copy code' }));
  expect(await screen.findByText(/Select the code and copy it manually/)).toBeInTheDocument();
  expect(alert).not.toHaveBeenCalled();
});

test('clears old sample choices and MeTTa when starting a new extraction', async () => {
  showGsmChoices();
  act(() => socket.onopen());
  send({ abstract_predicates: ['Gene(A)'] });
  global.fetch.mockResolvedValueOnce(response({ metta_valid: ['(Gene A)'] }));
  fireEvent.click(screen.getByRole('button', { name: 'Generate MeTTa Code' }));
  await screen.findByText('(Gene A)');
  global.fetch.mockResolvedValueOnce(response({ status: 'ok' }));
  fireEvent.click(screen.getByRole('button', { name: 'Parse' }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Parse' })).toBeEnabled());
  expect(screen.queryByText('(Gene A)')).not.toBeInTheDocument();
  expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
});
