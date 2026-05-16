import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { App } from '../src/App';

test('renders dashboard navigation and pipeline page', () => {
  render(<App />);
  expect(screen.getByRole('button', { name: 'Pipeline' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Services' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Logs' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'System' })).toBeInTheDocument();
  expect(screen.getByText('Text → Speech → Face')).toBeInTheDocument();
});
