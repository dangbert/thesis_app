import { render } from '@testing-library/react';

// import App from './app';
import Enroll from './user/Enroll';

import NotLoggedIn from './user/NotLoggedIn';

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

describe('Enroll', () => {
  it('should render successfully', () => {
    const { baseElement } = render(<Enroll />);
    expect(baseElement).toBeTruthy();
  });
});

describe('NotLoggedIn', () => {
  it('should render successfully', () => {
    const { baseElement } = render(<NotLoggedIn />);
    expect(baseElement).toBeTruthy();
  });
});
