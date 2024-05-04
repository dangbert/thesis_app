import React, { useContext } from 'react';
import { UserPublic } from './models';

export interface IUserProviderContext {
  user?: UserPublic;
  // handle login or logout
  onChange: (user?: UserPublic) => void;
}

export const UserContext = React.createContext<IUserProviderContext>({
  onChange: () => undefined, // dummy function
});
export const useUserContext = () => useContext(UserContext);
