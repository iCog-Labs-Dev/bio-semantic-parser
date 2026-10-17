export class RequestError extends Error {
  constructor(message, { status, kind, details } = {}) {
    super(message);
    this.status = status;
    this.kind = kind;
    this.details = details || message;
  }
}

export async function requestJson(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (error) {
    throw new RequestError('The server could not be reached.', {
      kind: 'network', details: error.message,
    });
  }
  if (!response.ok) {
    // Server diagnostics may contain tracebacks; show them only on request.
    let details = '';
    try { details = (await response.text()).slice(0, 4000); } catch { /* No body available. */ }
    throw new RequestError(`HTTP ${response.status}`, {
      status: response.status, details: `HTTP ${response.status}${details ? `\n${details}` : ''}`,
    });
  }
  try {
    return await response.json();
  } catch {
    throw new RequestError('The server returned an unreadable response.', { kind: 'response' });
  }
}

export function explainError(error) {
  if (error.kind === 'network') return 'We couldn’t reach the server. Check your connection, then try again.';
  if (error.status === 404) return 'The requested resource wasn’t found. Check the study or sample ID and try again.';
  if (error.status === 429) return 'The service is receiving too many requests. Wait a moment, then try again.';
  if (error.status === 401 || error.status === 403) {
    return 'The server denied this request. Ask the deployment owner to check access and service credentials.';
  }
  if (error.status >= 500) {
    return 'The server couldn’t complete this request. Try again; if it continues, share the technical details with the deployment owner.';
  }
  return 'The response couldn’t be used. Try again; if it continues, share the technical details with the deployment owner.';
}
