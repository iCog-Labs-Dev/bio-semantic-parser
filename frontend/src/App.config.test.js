import { render, screen } from '@testing-library/react';

delete process.env.REACT_APP_BACKEND_URL;
delete process.env.REACT_APP_BACKEND_WS_URL;
const App = require('./App').default;

test('renders a useful configuration notice instead of throwing during page load', () => {
  render(<App />);
  expect(screen.getByRole('alert')).toHaveTextContent('Server connection isn’t configured');
  expect(screen.getByRole('button', { name: 'Parse' })).toBeDisabled();
  expect(screen.getByRole('heading', { name: 'Semantic Parser' })).toBeInTheDocument();
});
