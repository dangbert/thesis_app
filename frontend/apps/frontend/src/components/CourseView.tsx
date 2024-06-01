import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  useTheme,
  Button,
  Alert,
  Tabs,
  Tab,
  Box,
  AppBar,
  Link,
} from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';
import AssignmentView from './AssignmentView';
import UserProfileModal from './user/UserProfileModal';
import * as models from '../models';
import * as courseApi from '../api';
import * as utils from '../utils';
import { useUserContext } from '../providers';
import Markdown from 'react-markdown';
import { useNavigate, useLocation } from 'react-router-dom';

interface CourseViewProps {
  course: models.CoursePublic;
  refreshCourse: () => void;
}

const CourseView: React.FC<CourseViewProps> = ({ course, refreshCourse }) => {
  const queryParams = new URLSearchParams(window.location.search);
  const navigate = useNavigate();
  const location = useLocation();
  // assignments in current course
  const [asList, setAsList] = useState<models.AssignmentPublic[]>([]);
  // curent visible assignment
  const [curAsId, setCurAsId] = useState<string | undefined>(
    queryParams.get('assignment') || undefined
  );
  const [loadingAssignments, setLoadingAssignments] = useState(true);
  const [userProfileOpen, setUserProfileOpen] = useState(false);
  const [mustCompleteProfile, setMustCompleteProfile] = useState(false);

  const userCtx = useUserContext();
  const isTeacher = course.your_role === models.CourseRole.TEACHER;
  const curAs = asList.find((as) => as.id === curAsId);

  useEffect(() => {
    const newVal = utils.isUndefined(course.your_group) && !isTeacher;
    // console.log(`updating mustCompleteProfile to: ${newVal}`);
    // console.log(`course.your_group = ${course.your_group}`);
    setMustCompleteProfile(newVal);
    setUserProfileOpen(newVal);
  }, [course.your_group, isTeacher]);

  // load assignments for current course
  useEffect(() => {
    let cancel = false;
    (async () => {
      setLoadingAssignments(true);
      const res = await courseApi.listAssignments(course.id);
      if (cancel) return;
      setLoadingAssignments(false);
      if (res.error) {
        console.error(res.error);
        setAsList([]);
      } else {
        const newAssignments = res.data as models.AssignmentPublic[];
        const preferredAs = newAssignments.find((x) => x.id === curAsId);
        if (!preferredAs) setCurAsId(newAssignments.at(0)?.id);
        setAsList(newAssignments);
      }

      return () => (cancel = true);
    })();
  }, [course.id]);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    // Update or set the course parameter to curCourseId
    if (curAs) {
      searchParams.set('course', curAs.id);
      searchParams.set('assignment', curAs.id);
    } else {
      searchParams.delete('assignment');
    }

    navigate(
      {
        pathname: location.pathname,
        search: `?${searchParams.toString()}`,
      },
      { replace: true }
    );
  }, [curAs?.id]);

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
          <Typography variant="h4" component="h3">
            {course.name}
          </Typography>
          <Typography variant="caption">
            You're a {course.your_role} in this course, and your group number is{' '}
            {utils.isUndefined(course.your_group)
              ? 'not set'
              : course.your_group}
            . <br />
            If you need to change your group number{' '}
            <Link onClick={() => setUserProfileOpen(true)}>click here.</Link>
          </Typography>
          <Markdown
            // make links open in a new page
            components={{
              a: ({ node, ...props }) => (
                <a {...props} target="_blank" rel="noopener noreferrer" />
              ),
            }}
          >
            {course.about}
          </Markdown>
        </CardContent>
      </Card>

      {/* force user to define group number */}
      {userProfileOpen && (
        <UserProfileModal
          course={course}
          open={userProfileOpen}
          onClose={
            mustCompleteProfile ? undefined : () => setUserProfileOpen(false)
          }
          onUpdate={refreshCourse}
        />
      )}

      <br />
      <br />

      {/* NOTE: UI for creating assignments not fully supported, easier to use DB client */}
      {/* {isTeacher && (
        <Button variant="contained" onClick={handleCreateAs}>
          Create Assignment
        </Button>
      )} */}

      {loadingAssignments && 'loading assignments...'}

      {!loadingAssignments && (
        <>
          {!asList.length && (
            <Alert severity="info">
              This course currently has no assignments
            </Alert>
          )}
          {asList.length > 0 && (
            <>
              <Typography>
                This course has {asList.length} assignment
                {asList.length === 0 ? '' : 's'}:
              </Typography>
              <Box sx={{ width: '100%' }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                  <Tabs
                    value={curAs ? curAs.id : false}
                    onChange={(event: React.SyntheticEvent, newValue: string) =>
                      setCurAsId(newValue.toString())
                    }
                    aria-label="Assignment Tabs"
                  >
                    {asList.map((as, idx) => (
                      <Tab
                        label={as.name}
                        value={as.id}
                        key={as.id}
                        {...a11yProps(idx)}
                      />
                    ))}
                  </Tabs>
                </Box>
                {asList.map((as, idx) => (
                  <CustomTabPanel
                    value={as.id}
                    curValue={curAsId || ''}
                    key={as.id}
                  >
                    <AssignmentView asData={as} isTeacher={isTeacher} />
                  </CustomTabPanel>
                ))}
              </Box>
            </>
          )}
        </>
      )}

      {/* {asData && <AssignmentView asData={asData} />} */}
    </div>
  );
};

interface TabPanelProps {
  children?: React.ReactNode;
  value: string;
  curValue: string; // visible tab's value
}

// https://mui.com/material-ui/react-tabs/#introduction
function CustomTabPanel(props: TabPanelProps) {
  const { children, value, curValue, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== curValue}
      id={`simple-tabpanel-${curValue}`}
      aria-labelledby={`simple-tab-${curValue}`}
      {...other}
    >
      {value === curValue && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`,
  };
}

export default CourseView;
