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
