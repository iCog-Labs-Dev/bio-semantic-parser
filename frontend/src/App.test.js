import { act, fireEvent, render, screen, within } from '@testing-library/react';

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
  expect(await screen.findByRole('alert')).toHaveTextContent('Unable to load GSM table: Failed to fetch');
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
