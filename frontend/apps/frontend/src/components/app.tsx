import React, { useState } from 'react';

import { BrowserRouter, Route, Routes } from 'react-router-dom';
import styled from '@emotion/styled';

import { ThemeProvider, Theme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import INITIAL_THEME, {
  CustomThemeContext,
  ICustomThemeProviderContext,
} from '../theme';
import Typography from '@mui/material/Typography';

import Onboard from './Onboard';
import HomePage from './HomePage';

const StyledApp = styled.div`
  // Your style here
`;

export function App() {
  const [theme, setTheme] = useState<Theme>(INITIAL_THEME);

  const customThemeCtx: ICustomThemeProviderContext = {
    theme: theme,
    setTheme: (newTheme: Theme) => {
      console.log('\nsetting new theme:\n', newTheme);
      setTheme(newTheme);
    },
  };

  return (
    <BrowserRouter>
      <StyledApp>
        <CustomThemeContext.Provider value={customThemeCtx}>
          {/* still using ThemeProvider for the sake of mui's components */}
          <ThemeProvider theme={customThemeCtx.theme}>
            <CssBaseline enableColorScheme={true} />
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/join" element={<Onboard />} />
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
                  <Typography variant="h1" gutterBottom>
                    Fallback page
                  </Typography>
                }
              />
            </Routes>
          </ThemeProvider>
        </CustomThemeContext.Provider>
      </StyledApp>
    </BrowserRouter>
  );
}

export default App;
