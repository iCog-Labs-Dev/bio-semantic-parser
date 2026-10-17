const isRecord = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);

export function parseGsmTable(data) {
  const invalidResponse = () => new Error('Invalid GSM table response.');
  if (!isRecord(data)) throw invalidResponse();

  const columns = Object.keys(data);
  if (!columns.every((column) => isRecord(data[column]))) throw invalidResponse();

  const rowKeys = columns.length > 0 ? Object.keys(data[columns[0]]) : [];
  for (const column of columns) {
    if (Object.keys(data[column]).length !== rowKeys.length) throw invalidResponse();
    for (const rowKey of rowKeys) {
      if (!Object.prototype.hasOwnProperty.call(data[column], rowKey)) throw invalidResponse();
      const value = data[column][rowKey];
      if (value !== null && !['string', 'number', 'boolean'].includes(typeof value)) {
        throw invalidResponse();
      }
    }
  }

  return { columns, rowKeys, data };
}
