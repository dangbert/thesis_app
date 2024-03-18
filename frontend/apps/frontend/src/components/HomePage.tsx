import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Link from '@mui/material/Link';

function HomePage() {
  return (
    <Typography variant="h1" gutterBottom>
      Welcome Home{' '}
      <Button variant="contained" href="/join">
        Onboard now!
      </Button>
      <Link href="/join">Onboard!</Link>
    </Typography>
  );
}

export default HomePage;
