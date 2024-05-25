import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  useTheme,
  Button,
  Alert,
} from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';
import AssignmentView from './AssignmentView';
import * as models from '../models';
import * as courseApi from '../api/courses';
import { useUserContext } from '../providers';

interface CourseViewProps {
  course: models.CoursePublic;
}

const CourseView: React.FC<CourseViewProps> = ({ course }) => {
  const [asList, setAsList] = useState<models.AssignmentPublic[]>([]); // assignments for current course
  const [asIdx, setAsIdx] = useState<number>(-1); // curent assignment index
  const [loadingAssignments, setLoadingAssignments] = useState<boolean>(true);

  const userCtx = useUserContext();
  const theme = useTheme();
  //   const classes = useStyles(theme);

  const isAdmin = false;

  const asData = asIdx > -1 && asIdx < asList.length ? asList[asIdx] : null;

  // load assignments for current course
  useEffect(() => {
    let cancel = false;
    (async () => {
      setLoadingAssignments(true);
      console.log(`requesting assignment list for course ${course.id}`);
      const res = await courseApi.listAssignments(course.id);
      if (cancel) return;
      setLoadingAssignments(false);
      if (res.error) {
        console.error(res.error);
        setAsList([]);
      } else {
        console.log('fetched assignment list\n', res.data);
        setAsList(res.data);
        setAsIdx(res.data.length > 0 ? 0 : -1);
      }

      return () => (cancel = true);
    })();
  }, [course.id]);

  const handleCreateAs = async () => {
    console.log('creating assignment');
    const dummyAs: models.AssignmentCreate = {
      name: 'dummy assignment',
      about: '**more info to come**\n:)',
      scorable: false,
    };
    const response = await courseApi.createAssignment(course.id, dummyAs);
    if (!response.error) {
      console.log('Assignment created:', response.data);
      setAsList((prev) => [...prev, response.data]);
    } else {
      console.error('Error creating assignment:', response.error);
    }
  };

  if (!userCtx.user) return null;
  return (
    <div>
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h3" component="h2">
            {course.name}
          </Typography>
          <Typography variant="body2" color="textSecondary" component="p">
            {course.about}
          </Typography>
        </CardContent>
      </Card>
      <hr />
      <br />
      <br />

      {/*map courselist to simple list of names */}
      {loadingAssignments && 'loading assignments...'}

      {!loadingAssignments && !asList.length && (
        <Alert severity="info">This course currently has no assignments</Alert>
      )}

      {isAdmin && (
        <Button variant="contained" onClick={handleCreateAs}>
          Create Assignment
        </Button>
      )}

      {asData && <AssignmentView asData={asData} />}
    </div>
  );
};

export default CourseView;
