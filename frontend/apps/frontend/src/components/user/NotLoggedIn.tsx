import { Button, Card, Typography } from '@mui/material';
import * as constants from '../../constants';

const NotLoggedIn = () => {
  return (
    <>
      {/* <Button variant="contained" href="/join">
          Onboard now!
        </Button> */}
      <br />
      <Card
        variant="outlined"
        sx={{ padding: '14px', maxWidth: '1100px', marginLeft: '20px' }}
      >
        <Typography variant="h4" gutterBottom>
          You're not logged in.
        </Typography>
        <Typography variant="h5" gutterBottom sx={{ fontStyle: 'bold' }}>
          You can login to an existing account below, otherwise ask your teacher
          for an invite link to signup.
        </Typography>
        <Button
          size="large"
          variant="contained"
          href={constants.LOGIN_URL}
          // onClick={handleRedirect}
        >
          Login
        </Button>
        <Typography variant="h6" gutterBottom></Typography>
      </Card>
    </>
  );
};

export default NotLoggedIn;
