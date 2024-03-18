import React, { useContext } from 'react';
import { createTheme } from '@mui/material/styles';
import { Theme } from '@mui/material/styles';

const INITIAL_THEME = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#3c8a45',
    },
    // secondary: {
    // main: '#c35e0b',
    // },
    secondary: {
      //main: '#d44b56',
      main: '#b5736c',
    },
  },
  components: {
    MuiLink: {
      defaultProps: {
        underline: 'hover',
      },
    },
  },
});

//// current theme ////
export interface ICustomThemeProviderContext {
  theme: Theme;
  setTheme: (new_theme: Theme) => void;
}
export const CustomThemeContext =
  React.createContext<ICustomThemeProviderContext>({
    theme: INITIAL_THEME,
    setTheme: () => false, // dummy function
  });
// https://stackoverflow.com/a/66227617/5500073
export const useCustomTheme = () => useContext(CustomThemeContext);

export default INITIAL_THEME;
