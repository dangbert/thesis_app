import { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  CardActions,
  Alert,
  CircularProgress,
} from '@mui/material';
import { LOGIN_URL } from '../../constants';
import { useParams } from 'react-router-dom';
import * as models from '../../models';
import * as api from '../../api';
import * as constants from '../../constants';

/**
 * Component for user to join by invite key.
 */
export default function Enroll() {
  const message = 'Login with your VU email to join!';
  const { inviteKey } = useParams();
  const [error, setError] = useState('');
  const [course, setCourse] = useState<models.CoursePublic | null>();
  const [loading, setLoading] = useState(true);

  // const handleRedirect = () => {
  //   window.location.href = LOGIN_URL; // force page reload
  // };

  // load course list
  useEffect(() => {
    let cancel = false;
    if (!inviteKey) {
      setError('invite key not provided');
      setLoading(false);
      window.location.href = '/';
      return;
    }
    (async () => {
      console.log('requesting course list');
      setLoading(true);
      const res = await api.getEnrollDetails(inviteKey);
      if (cancel) return;
      setLoading(false);
      if (res.error) {
        setError(res.error);
        setCourse(null);
      } else {
        setCourse(res.data);
      }
      return () => (cancel = true);
    })();
  }, [inviteKey]);

  const targetRole = course?.invite_role || models.CourseRole.STUDENT;
  return (
    <Card sx={{ maxWidth: 400, m: 'auto', mt: 5 }}>
      {error && (
        <>
          <Alert severity="error">{error}</Alert>
          <br />
          <Button href="/">Visit Home Page</Button>
        </>
      )}

      {loading && (
        <CardContent>
          <Typography variant="h5">Loading course invite details...</Typography>
          <CircularProgress />
        </CardContent>
      )}
      {course && (
        <>
          <CardContent>
            <Typography variant="h5" component="div">
              You're invited to join as a {targetRole}.
            </Typography>
            <Typography sx={{ mt: 2 }}>Course: {course.name}</Typography>
            <Typography sx={{ mt: 2 }}>{message}</Typography>
          </CardContent>
          <CardActions>
            <Button
              size="large"
              variant="contained"
              sx={{ width: '100%' }}
              href={`${LOGIN_URL}?invite_key=${inviteKey}`}
              // onClick={handleRedirect}
            >
              Join Course
            </Button>
          </CardActions>
        </>
      )}
    </Card>
  );
}
