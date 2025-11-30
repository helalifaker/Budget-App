import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders scaffold heading', () => {
    render(<App />);
    expect(screen.getByText(/Frontend scaffold ready/i)).toBeInTheDocument();
  });
});
