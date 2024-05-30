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
  Alert,
  Card,
  Tooltip,
} from '@mui/material';
import ListItemIcon from '@mui/material/ListItemIcon';
import MenuIcon from '@mui/icons-material/Menu';
import LogoutIcon from '@mui/icons-material/Logout';

import makeStyles from '@mui/styles/makeStyles';
import CourseView from './CourseView';

import { useUserContext } from '../providers';
import * as models from '../models';
import * as courseApi from '../api';
import * as constants from '../constants';
import * as utils from '../utils';
import NotLoggedIn from './user/NotLoggedIn';

const HomePage = () => {
  const [courseList, setCourseList] = useState<models.CoursePublic[]>([]);
  const [loadingCourses, setLoadingCourses] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [courseIdx, setCourseIdx] = useState<number>(-1);
  const userCtx = useUserContext();
  const theme = useTheme();
  const classes = useStyles(theme);
  const [userMenuEl, setUserMenuEl] = useState<HTMLElement | null>(null);

  // TODO: refresh user data on a timer, alert user if they're logged out
  // "login in a new tab if you wish to continue your work on this page"
  useEffect(() => {
    (async () => {
      let cancel = false;
      const res = await courseApi.getCurUser();
      if (cancel) return;
      if (res.error) {
        console.error(`failed to load current user: ${res.error}`);
        setError(`failed to load current user: ${res.error}`);
      } else {
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
      setLoadingCourses(true);
      const res = await courseApi.listCourses();
      if (cancel) return;
      setLoadingCourses(false);
      if (res.error) {
        console.error(res.error);
        setCourseList([]);
        setError(`failed to load course list: ${res.error}`);
      } else {
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

  const handleLogout = () => {
    window.location.href = courseApi.LOGOUT_URL; // force page reload
  };

  if (!userCtx.user) return <NotLoggedIn />;
  return (
    <div className={classes.fullHeightDiv}>
      {/* header bar */}
      <AppBar position="sticky">
        <Toolbar>
          {/* <IconButton edge="start" color="inherit" aria-label="menu">
            <MenuIcon />
          </IconButton> */}
          <Typography
            variant="h6"
            style={{ flexGrow: 1, marginLeft: theme.spacing(2) }}
          >
            EzFeedback
          </Typography>
          <div>
            <Tooltip title={`Logged in as ${userCtx.user.email}`}>
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
            </Tooltip>

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
                  <LogoutIcon />
                </ListItemIcon>
                <ListItemText primary="Logout" />
              </MenuItem>
            </Menu>
          </div>
        </Toolbar>
      </AppBar>

      {/* main content */}
      {error && <Alert severity="error">{error}</Alert>}

      <div className={classes.centeredContent}>
        {/*map courselist to simple list of names */}
        {loadingCourses && 'loading courses...'}

        {!loadingCourses && courseList.length === 0 && (
          <Alert severity="warning">
            You're not enrolled in any courses yet, ask your teacher for an
            invite link...
          </Alert>
        )}
        {curCourse && <CourseView course={curCourse} />}
      </div>
    </div>
  );
};

function stringAvatar(name: string) {
  return {
    sx: {
      bgcolor: utils.stringToColor(name),
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
    overflowY: 'scroll', // Optional: to manage overflow of child components
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
