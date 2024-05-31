import { Avatar } from '@mui/material';
import * as models from '../../models';
import * as utils from '../../utils';

interface UserAvatarProps {
  user: models.UserPublic;
  // TODO: sizePx doesn't change the font size of the initals
  sizePx?: number;
}

/**
 * Display user's initials in a colored circle.
 */
const UserAvatar: React.FC<UserAvatarProps> = ({ user, sizePx }) => {
  const variant = 'circular';
  const sx = sizePx ? { width: '18px', height: '18px' } : {};

  const defaultSx = { ...stringAvatar(user.name) }.sx;
  const stringProps = sizePx
    ? {
        ...stringAvatar(user.name),
        sx: { ...defaultSx, width: sizePx, height: sizePx },
      }
    : stringAvatar(user.name);
  return (
    <>
      {user.picture && (
        <Avatar sx={sx} alt={user.name} src={user.picture} variant={variant} />
      )}
      {!user.picture && <Avatar {...stringProps} variant={variant} />}
    </>
  );
};

// TODO: unit test this can handle weird names
function stringAvatar(name: string) {
  const names = name.split(' ');
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
