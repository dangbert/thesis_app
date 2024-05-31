import { Avatar } from '@mui/material';
import * as models from '../../models';
import * as utils from '../../utils';

interface UserAvatarProps {
  user: models.UserPublic;
}

/**
 * Display user's initials in a colored circle.
 */
const UserAvatar: React.FC<UserAvatarProps> = ({ user }) => {
  console.log('user avatar, ', user);
  return (
    <>
      {user.picture && <Avatar alt={user.name} src={user.picture} />}
      {!user.picture && <Avatar {...stringAvatar(user.name)} />}
    </>
  );
};

// TODO: unit test this can handle weird names
function stringAvatar(name: string) {
  const names = name.split(' ');
  console.log('names=');
  console.log(names);
  // safely read considering name could be empty string etc
  const firstInitial = names[0] ? names[0][0] : '';
  const lastInitial = names[names.length - 1] ? names[names.length - 1][0] : '';
  return {
    sx: {
      bgcolor: utils.stringToColor(name),
    },
    children: `${firstInitial.toUpperCase()}${(lastInitial
      ? lastInitial
      : ''
    ).toUpperCase()}`,
  };
}

export default UserAvatar;
