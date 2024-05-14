import { useEffect, useState } from 'react';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Button,
  Link,
  Avatar,
  useTheme,
  Menu,
  MenuItem,
  ListItemText,
  Icon,
} from '@mui/material';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import ListItemIcon from '@mui/material/ListItemIcon';

import MenuIcon from '@mui/icons-material/Menu';
import makeStyles from '@mui/styles/makeStyles';
import AssignmentView from './AssignmentView';

import { useUserContext } from '../providers';
import * as models from '../models';
import * as courseApi from '../api/courses';

const HomePage = () => {
  const [courseList, setCourseList] = useState<models.CoursePublic[]>([]);
  const [courseIdx, setCourseIdx] = useState<number>(-1);
  const [asList, setAsList] = useState<models.AssignmentPublic[]>([]); // assignments for current course
  const [asIdx, setAsIdx] = useState<number>(-1); // curent assignment index
  const userCtx = useUserContext();
  const classes = useStyles();
  const theme = useTheme();
  const [userMenuEl, setUserMenuEl] = useState<HTMLElement | null>(null);

  useEffect(() => {
    const dummyUser = {
      created_at: '2024-05-12T13:13:47.346969Z',
      updated_at: undefined,
      sub: 'auth0|4005879303709086033',
      name: 'Dan Engbert',
      email: 'd.engbert@student.vu.nl',
      id: '6b3c87e9-7ad2-407b-bb29-c8ab919bda5d',
      profileUrl: undefined,
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

  const handleLogout = async () => {
    const res = await courseApi.logout();
    if (res.error) {
      alert(`failed to logout: ${res.error}`);
    } else {
      userCtx.onChange(undefined);
      setUserMenuEl(null); // close user menu
    }
  };

  if (!userCtx.user) return; // TODO: redirect to login page?

  const themePrimaryColor = theme.palette.primary.main;
  return (
    <div className={classes.fullHeightDiv}>
      {/* header bar */}
      <AppBar position="static">
        <Toolbar>
          {/* <IconButton edge="start" color="inherit" aria-label="menu">
            <MenuIcon />
          </IconButton> */}
          <Typography variant="h6" style={{ flexGrow: 1, marginLeft: '5px' }}>
            Ezfeedback
          </Typography>
          <div>
            <IconButton
              onClick={(event: React.MouseEvent<HTMLButtonElement>) => {
                if (userCtx.user) setUserMenuEl(event.currentTarget); // open user menu
              }}
            >
              {userCtx.user && userCtx.user.picture ? (
                <Avatar alt={userCtx.user.name} src={userCtx.user.picture} />
              ) : (
                <Avatar {...stringAvatar(userCtx.user.name)} />
              )}
            </IconButton>

            <Menu
              anchorEl={userMenuEl}
              keepMounted
              open={Boolean(userMenuEl)}
              onClose={() => setUserMenuEl(null)}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
              transformOrigin={{ vertical: 'top', horizontal: 'left' }}
            >
              <MenuItem onClick={handleLogout}>
                <ListItemIcon>
                  <LockOpenIcon />
                </ListItemIcon>
                <ListItemText primary="Logout" />
              </MenuItem>
            </Menu>
          </div>
        </Toolbar>
      </AppBar>

      {/* main content */}
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

function getInitials(name: string): string {
  const firstname = name.split(' ')[0];
  // get last name considering there may be a middle name
  const lastname = name.split(' ').slice(-1)[0];
  if (name.split(' ').length >= 2) {
    return firstname[0] + lastname[0];
  }
  return firstname[0];
}

// from https://mui.com/material-ui/react-avatar/#letter-avatars
function stringToColor(string: string) {
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

function stringAvatar(name: string) {
  return {
    sx: {
      bgcolor: stringToColor(name),
    },
    children: `${name.split(' ')[0][0]}${name.split(' ')[1][0]}`,
  };
}

const useStyles = makeStyles((theme) => ({
  fullHeightDiv: {
    height: '100vh',
    width: '100vw',
    margin: 0,
    padding: 0,
    overflow: 'hidden', // Optional: to manage overflow of child components
    border: '2px dashed red',
  },
}));

export default HomePage;
