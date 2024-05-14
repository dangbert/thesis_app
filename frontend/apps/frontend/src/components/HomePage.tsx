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
import CourseView from './CourseView';

import { useUserContext } from '../providers';
import * as models from '../models';
import * as courseApi from '../api/courses';

const HomePage = () => {
  const [courseList, setCourseList] = useState<models.CoursePublic[]>([]);
  const [loadingCourses, setLoadingCourses] = useState<boolean>(true);
  const [courseIdx, setCourseIdx] = useState<number>(-1);
  const userCtx = useUserContext();
  const theme = useTheme();
  const classes = useStyles(theme);
  const [userMenuEl, setUserMenuEl] = useState<HTMLElement | null>(null);

  // TODO: referesh user data on a timer?
  useEffect(() => {
    (async () => {
      let cancel = false;
      const res = await courseApi.getCurUser();
      if (cancel) return;
      if (res.error) {
        console.error(`failed to load current user: ${res.error}`);
      } else {
        console.log('fetched attempt list\n', res.data);
        console.log('loaded user:');
        console.log(res.data);
        userCtx.onChange(res.data);
      }

      return () => (cancel = true);
    })();
  }, []);

  // load course list
  useEffect(() => {
    let cancel = false;
    (async () => {
      console.log('requesting course list');
      setLoadingCourses(true);
      const res = await courseApi.listCourses();
      if (cancel) return;
      setLoadingCourses(false);
      if (res.error) {
        console.error(res.error);
        setCourseList([]);
      } else {
        console.log('fetched course list\n', res.data);
        setCourseIdx(res.data.length > 0 ? 0 : -1);
        setCourseList(res.data);
      }
      return () => (cancel = true);
    })();
  }, []);

  const curCourse =
    courseIdx > -1 && courseIdx < courseList.length
      ? courseList[courseIdx]
      : null;

  const handleLogout = async () => {
    const res = await courseApi.logout();
    if (res.error) {
      alert(`failed to logout: ${res.error}`);
    } else {
      userCtx.onChange(undefined);
      setUserMenuEl(null); // close user menu
    }
  };

  if (!userCtx.user) {
    return (
      <>
        <div>not logged in...</div>
        <Button variant="contained" href="/join">
          Onboard now!
        </Button>
      </>
    );
  }

  return (
    <div className={classes.fullHeightDiv}>
      {/* header bar */}
      <AppBar position="static">
        <Toolbar>
          {/* <IconButton edge="start" color="inherit" aria-label="menu">
            <MenuIcon />
          </IconButton> */}
          <Typography
            variant="h6"
            style={{ flexGrow: 1, marginLeft: theme.spacing(2) }}
          >
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

      <div className={classes.centeredContent}>
        {/*map courselist to simple list of names */}
        {loadingCourses && 'loading courses...'}

        {!loadingCourses &&
          courseList.length === 0 &&
          "You're not enrolled in any courses yet..."}

        {curCourse && <CourseView course={curCourse} />}
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
  centeredContent: {
    display: 'flex',
    // justifyContent: 'center',
    alignItems: 'center',
    padding: '20px',
    margin: 'auto',
    // TODO: use breakpoitn
    //maxWidth: `${theme.breakpoints.values.lg}px`,
    maxWidth: `1500px`,
    // border: '2px dashed green',
  },
}));

export default HomePage;
