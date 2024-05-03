import { render } from '@testing-library/react';

// import App from './app';
import Onboard from './Onboard';

// disabled due to ReferenceError: fetch is not defined
/*
describe('App', () => {
  it('should render successfully', () => {
    const { baseElement } = render(<App />);
    expect(baseElement).toBeTruthy();
  });

  it('should have a greeting as the title', () => {
    const { getByText } = render(<App />);
    expect(getByText(/Welcome Home/gi)).toBeTruthy();
  });
});
*/

describe('Onboard', () => {
  it('should render successfully', () => {
    const { baseElement } = render(<Onboard />);
    expect(baseElement).toBeTruthy();
  });
});
