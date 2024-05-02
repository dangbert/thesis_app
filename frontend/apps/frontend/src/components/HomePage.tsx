import { useEffect, useState } from 'react';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Link from '@mui/material/Link';
import AssignmentView from './Assignment';

import * as models from '../models';
import * as courseApi from '../api/courses';

const HomePage = () => {
  const [courseList, setCourseList] = useState<models.CoursePublic[]>([]);

  useEffect(() => {
    let cancel = false;
    (async () => {
      console.log('requesting course list');
      const res = await courseApi.listCourses();
      if (cancel) return;
      if (res.error) {
        console.error(res.error);
      } else {
        console.log('fetched course list\n', res.data);
        setCourseList(res.data);
      }

      return () => {
        cancel = true;
      };
    })();
  }, []);

  return (
    <div>
      <Typography variant="h1" gutterBottom>
        Welcome Home{' '}
        <Button variant="contained" href="/join">
          Onboard now!
        </Button>
        <Link href="/join">Onboard!</Link>
      </Typography>
      <div style={{ border: '2px solid purple' }}>
        {/* <AssignmentView
          name="Smart"
          about="This is the first assignment"
          id="f46eb7bd-ddbe-4553-b72f-d4f35d08c5f8"
        /> */}

        {/*map courselist to simple list of names */}
        {courseList.map((course) => (
          <div key={course.id}>
            <Typography variant="h3">{course.name}</Typography>
            <Typography variant="body1">{course.about}</Typography>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HomePage;
