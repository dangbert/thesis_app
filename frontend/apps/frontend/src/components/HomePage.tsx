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
import UserAvatar from './user/UserAvatar';
import { useNavigate, useLocation } from 'react-router-dom';

const HomePage = () => {
  const queryParams = new URLSearchParams(window.location.search);
  const navigate = useNavigate();
  const location = useLocation();
  const [courseList, setCourseList] = useState<models.CoursePublic[]>([]);
  const [reloadTime, setReloadTime] = useState<number>(Date.now() / 1000);
  const [loadingCourses, setLoadingCourses] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [curCourseId, setCurCourseId] = useState<string | undefined>(
    queryParams.get('course') || undefined
  );

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
        userCtx.onChange(res.data);
      }

      return () => (cancel = true);
    })();
  }, [reloadTime]);

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
        const newCourses = res.data as models.CoursePublic[];
        const preferredCourse = newCourses.find((c) => c.id === curCourseId);
        if (!preferredCourse) setCurCourseId(newCourses.at(0)?.id);
        setCourseList(newCourses);
      }
      return () => (cancel = true);
    })();
  }, [reloadTime, curCourseId]);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    if (curCourseId) {
      searchParams.set('course', curCourseId);
    } else {
      searchParams.delete('course');
    }

    navigate(
      {
        pathname: location.pathname,
        search: `?${searchParams.toString()}`,
      },
      { replace: true }
    );
  }, [curCourseId]);

  const curCourse = courseList.find((c) => c.id === curCourseId);

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
                {userCtx.user && <UserAvatar user={userCtx.user} />}
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
        {curCourse && (
          <CourseView
            course={curCourse}
            refreshCourse={() => setReloadTime(Date.now() / 1000)}
          />
        )}
      </div>
    </div>
  );
};

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
