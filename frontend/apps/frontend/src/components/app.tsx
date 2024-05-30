import { useState, useEffect } from 'react';

import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom';
import styled from '@emotion/styled';
import { ThemeProvider, Theme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import INITIAL_THEME, {
  CustomThemeContext,
  ICustomThemeProviderContext,
} from '../theme';
import Typography from '@mui/material/Typography';

import Enroll from './user/Enroll';
import HomePage from './HomePage';

import { IUserProviderContext, UserContext } from '../providers';
import * as models from '../models';
import '../app.css';

const StyledApp = styled.div`
  // Your style here
`;

export function App() {
  const [theme, setTheme] = useState<Theme>(INITIAL_THEME);
  const [user, setUser] = useState<models.UserPublic | undefined>(undefined);

  const customThemeCtx: ICustomThemeProviderContext = {
    theme: theme,
    setTheme: (newTheme: Theme) => {
      console.log('\nsetting new theme:\n', newTheme);
      setTheme(newTheme);
    },
  };

  const userContext: IUserProviderContext = {
    user,
    onChange: (newUser?: models.UserPublic) => setUser(newUser),
  };

  return (
    <BrowserRouter>
      {/* <StyledApp> */}
      <CustomThemeContext.Provider value={customThemeCtx}>
        {/* still using ThemeProvider for the sake of mui's components */}
        <ThemeProvider theme={customThemeCtx.theme}>
          <UserContext.Provider value={userContext}>
            <CssBaseline enableColorScheme={true} />
            <Routes>
              {/* if user got soft linked to a /api url, refresh the page */}
              <Route path="/api/*" element={<ApiRedirect />} />
              <Route path="/" element={<HomePage />} />
              <Route path="/enroll/:inviteKey" element={<Enroll />} />
              <Route
                path="/test"
                element={
                  <Typography variant="h2" gutterBottom>
                    Testing
                  </Typography>
                }
              />

              <Route
                path="*"
                element={
                  <Typography
                    variant="h4"
                    gutterBottom
                    style={{
                      display: 'flex',
                      justifyContent: 'center',
                      marginTop: '24px',
                    }}
                  >
                    Page not found...{' '}
                    <a href="/" style={{ marginLeft: '8px' }}>
                      {' '}
                      go to home page
                    </a>
                  </Typography>
                }
              />
            </Routes>
          </UserContext.Provider>
        </ThemeProvider>
      </CustomThemeContext.Provider>
      {/* </StyledApp> */}
    </BrowserRouter>
  );
}

const ApiRedirect = () => {
  const location = useLocation();

  useEffect(() => {
    // Check if the current path starts with '/api'
    if (location.pathname.startsWith('/api')) {
      // Force a full page reload to the current path
      window.location.href =
        window.location.origin + location.pathname + location.search;
    }
  }, [location]);

  return 'redirecting...';
};

export default App;
