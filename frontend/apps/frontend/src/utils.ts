export const friendlyDate = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleString([], {
    month: 'short', // "May"
    day: '2-digit', // "24"
    year: 'numeric', // "2024"
    hour: '2-digit', // "10"
    minute: '2-digit', // "25"
    hour12: true, // use AM/PM
  });
};

/**
 * Get a user's initials from their name.
 */
export function getInitials(name: string): string {
  const firstname = name.split(' ')[0];
  // get last name considering there may be a middle name
  const lastname = name.split(' ').slice(-1)[0];
  if (name.split(' ').length >= 2) {
    return firstname[0] + lastname[0];
  }
  return firstname[0];
}

// from https://mui.com/material-ui/react-avatar/#letter-avatars
export function stringToColor(string: string): string {
  let hash = 0;
  let i;

  /* eslint-disable no-bitwise */
  for (i = 0; i < string.length; i += 1) {
    hash = string.charCodeAt(i) + ((hash << 5) - hash);
  }

  let color = '#';
  for (i = 0; i < 3; i += 1) {
    const value = (hash >> (i * 8)) & 0xff;
    color += `00${value.toString(16)}`.slice(-2);
  }
  /* eslint-enable no-bitwise */
  return color;
}

/**
 * return true if value is null or undefined
 */
export function isUndefined(value: any): boolean {
  return value === null || value === undefined;
}
