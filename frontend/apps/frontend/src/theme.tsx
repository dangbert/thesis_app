import React, { useContext } from 'react';
import { createTheme } from '@mui/material/styles';
import { Theme } from '@mui/material/styles';

import {
  Link as RouterLink,
  LinkProps as RouterLinkProps,
} from 'react-router-dom';
import { LinkProps } from '@mui/material/Link';

// https://mui.com/material-ui/integrations/routing/#global-theme-link
const LinkBehavior = React.forwardRef<
  HTMLAnchorElement,
  Omit<RouterLinkProps, 'to'> & { href: RouterLinkProps['to'] }
>((props, ref) => {
  const { href, ...other } = props;
  // Map href (Material UI) -> to (react-router)
  return <RouterLink ref={ref} to={href} {...other} />;
});

const INITIAL_THEME = createTheme({
  palette: {
    mode: 'dark',
    // https://brandportal.vu.nl/modules/product/DigitalStyleGuide/default/index.aspx?ItemId=6744
    primary: {
      main: '#0077b3',
    },
    secondary: {
      main: '#008053',
    },
  },
  components: {
    MuiLink: {
      defaultProps: {
        // underline: 'hover',
        component: LinkBehavior,
      } as LinkProps,
    },
    MuiButtonBase: {
      defaultProps: {
        LinkComponent: LinkBehavior,
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
