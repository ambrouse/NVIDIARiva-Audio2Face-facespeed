import '@testing-library/jest-dom';
import { fireEvent, render, screen } from '@testing-library/react';
import { App } from '../src/App';

test('renders studio navigation and avatar composer', () => {
  render(<App />);
  expect(screen.getByRole('button', { name: 'Studio' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Operations' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Activity' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Setup' })).toBeInTheDocument();
  expect(screen.getByText('Create a speaking 3D avatar')).toBeInTheDocument();
  expect(screen.getByText('FaceSpeed Studio')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Generate avatar speech' })).toBeInTheDocument();
});

test('renders system safety commands and localhost ports', () => {
  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: 'Setup' }));
  expect(screen.getByText('127.0.0.1:8020')).toBeInTheDocument();
  expect(screen.getByText('127.0.0.1:6310')).toBeInTheDocument();
  expect(screen.getByText('127.0.0.1:50051')).toBeInTheDocument();
  expect(screen.getByText('127.0.0.1:8040')).toBeInTheDocument();
  expect(screen.getByText('bash scripts/setup.sh --dry-run-nvidia-full')).toBeInTheDocument();
});

test('disables pipeline run button for empty text', () => {
  render(<App />);
  const input = screen.getByLabelText('Script');
  fireEvent.change(input, { target: { value: '   ' } });
  expect(screen.getByRole('button', { name: 'Generate avatar speech' })).toBeDisabled();
});
