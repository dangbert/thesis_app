import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { CardActions } from '@mui/material';
import { LOGIN_URL } from '../constants';

function Onboard() {
  const courseName =
    'Project moderne ontwikkelingen in de farmaceutische wetenschappen';
  const instructors = ['Danny', 'Fanny'];
  const message = 'Login with your VU email to join!';
  const role = 'student';

  return (
    <Card sx={{ maxWidth: 400, m: 'auto', mt: 5 }}>
      <CardContent>
        <Typography variant="h5" component="div">
          You're invited to join as a {role}.
        </Typography>
        <Typography sx={{ mt: 2 }}>Course: {courseName}</Typography>
        <Typography>
          Instructor{instructors.length > 1 ? 's' : ''}:{' '}
          {instructors.join(', ')}
        </Typography>
        <Typography sx={{ mt: 2 }}>{message}</Typography>
      </CardContent>
      <CardActions>
        <Button
          size="large"
          variant="contained"
          sx={{ width: '100%' }}
          href={LOGIN_URL}
        >
          Join Course
        </Button>
      </CardActions>
    </Card>
  );
}

export default Onboard;
