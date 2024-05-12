import { useEffect, useState } from 'react';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Link from '@mui/material/Link';
import AssignmentView from './AssignmentView';

import { useUserContext } from '../providers';
import * as models from '../models';
import * as courseApi from '../api/courses';

const HomePage = () => {
  const [courseList, setCourseList] = useState<models.CoursePublic[]>([]);
  const [courseIdx, setCourseIdx] = useState<number>(-1);
  // assignments for current course
  const [asList, setAsList] = useState<models.AssignmentPublic[]>([]);
  // curent assignment index
  const [asIdx, setAsIdx] = useState<number>(-1);
  const userCtx = useUserContext();

  useEffect(() => {
    const dummyUser = {
      created_at: '2024-05-12T13:13:47.346969Z',
      updated_at: undefined,
      sub: 'auth0|4005879303709086033',
      name: 'Dan Engbert',
      email: 'd.engbert@student.vu.nl',
      id: '6b3c87e9-7ad2-407b-bb29-c8ab919bda5d',
    };
    userCtx.onChange(dummyUser);

    let cancel = false;
    (async () => {
      return () => (cancel = true);
    })();
  }, []);

  // load course list
  useEffect(() => {
    let cancel = false;
    (async () => {
      console.log('requesting course list');
      const res = await courseApi.listCourses();
      if (cancel) return;
      if (res.error) {
        console.error(res.error);
        setCourseList([]);
      } else {
        console.log('fetched course list\n', res.data);
        setCourseList(res.data);
        setCourseIdx(res.data.length > 0 ? 0 : -1);
      }
      return () => (cancel = true);
    })();
  }, []);

  // load assignments for current course
  useEffect(() => {
    let cancel = false;
    (async () => {
      if (courseIdx < 0 || courseIdx >= courseList.length) {
        setAsList([]);
        return;
      }
      const courseId = courseList[courseIdx].id;
      console.log(`requesting assignment list for course ${courseId}`);
      const res = await courseApi.listAssignments(courseId);
      if (cancel) return;
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
  }, [
    courseIdx,
    // cur course ID or -1
    courseIdx >= 0 && courseIdx < courseList.length
      ? courseList[courseIdx].id
      : -1,
  ]);

  const curCourse =
    courseIdx > -1 && courseIdx < courseList.length
      ? courseList[courseIdx]
      : null;
  const asData = asIdx > -1 && asIdx < asList.length ? asList[asIdx] : null;

  const handleCreateAs = async () => {
    if (!userCtx.user || !curCourse) return;
    console.log('creating assignment');
    const dummyAs: models.AssignmentCreate = {
      name: 'dummy assignment',
      about: '**more info to come**\n:)',
    };
    const response = await courseApi.createAssignment(curCourse.id, dummyAs);
    if (!response.error) {
      console.log('Assignment created:', response.data);
      setAsList((prev) => [...prev, response.data]);
    } else {
      console.error('Error creating assignment:', response.error);
    }
  };
  if (!userCtx.user) return; // TODO: redirect to login page?

  return (
    <div>
      <Typography variant="h1" gutterBottom>
        Welcome Home {userCtx.user?.name}
      </Typography>
      <Typography variant="body1">
        there are {courseList.length} courses + {asList.length} assignments
      </Typography>
      <br />

      <Button variant="contained" onClick={handleCreateAs}>
        Create Assignment
      </Button>

      <Button variant="contained" href="/join">
        Onboard now!
      </Button>
      <Link href="/join">Onboard!</Link>

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
        <hr />
        {asData && (
          <>
            <Typography variant="h3" gutterBottom>
              Your Assignment:
            </Typography>
            <AssignmentView asData={asData} />
          </>
        )}
      </div>
    </div>
  );
};

export default HomePage;
