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
 * Uses email as a deterministic color selector.
 */
const UserAvatar: React.FC<UserAvatarProps> = ({ user, sizePx }) => {
  const variant = 'circular';
  const sx = sizePx ? { width: '18px', height: '18px' } : {};

  const defaultSx = { ...stringAvatar(user.name) }.sx;
  const stringProps = sizePx
    ? {
        ...stringAvatar(user.name, user.email),
        sx: { ...defaultSx, width: sizePx, height: sizePx },
      }
    : stringAvatar(user.name, user.email);
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
function stringAvatar(name: string, email?: string) {
  const names = name.split(' ');
  // safely read considering name could be empty string etc
  const firstInitial = names[0] ? names[0][0] : '';
  const lastInitial = names[names.length - 1] ? names[names.length - 1][0] : '';
  return {
    sx: {
      // use email for color if possible (e.g. test accounts may have same name but different emails)
      bgcolor: utils.stringToColor(email ? email : name),
    },
    children: `${firstInitial.toUpperCase()}${(lastInitial
      ? lastInitial
      : ''
    ).toUpperCase()}`,
  };
}

export default UserAvatar;
