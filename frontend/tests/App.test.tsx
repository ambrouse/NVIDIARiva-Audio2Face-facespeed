import '@testing-library/jest-dom';
import { fireEvent, render, screen } from '@testing-library/react';
import { App } from '../src/App';

test('renders dashboard navigation and pipeline page', () => {
  render(<App />);
  expect(screen.getByRole('button', { name: 'Pipeline' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Services' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Logs' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'System' })).toBeInTheDocument();
  expect(screen.getByText('Text → Speech → Face')).toBeInTheDocument();
  expect(screen.getByText('Local mock-safe')).toBeInTheDocument();
  expect(screen.getByText(/127.0.0.1:8020/)).toBeInTheDocument();
});

test('renders system safety commands and localhost ports', () => {
  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: 'System' }));
  expect(screen.getByText('127.0.0.1:8020')).toBeInTheDocument();
  expect(screen.getByText('127.0.0.1:6210')).toBeInTheDocument();
  expect(screen.getByText('127.0.0.1:50100')).toBeInTheDocument();
  expect(screen.getByText('127.0.0.1:8040')).toBeInTheDocument();
  expect(screen.getByText('bash scripts/setup.sh --dry-run-nvidia-full')).toBeInTheDocument();
});

test('disables pipeline run button for empty text', () => {
  render(<App />);
  const input = screen.getByLabelText('Text input');
  fireEvent.change(input, { target: { value: '   ' } });
  expect(screen.getByRole('button', { name: 'Run pipeline' })).toBeDisabled();
});
