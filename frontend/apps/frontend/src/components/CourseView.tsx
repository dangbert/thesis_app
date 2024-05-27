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
} from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';
import AssignmentView from './AssignmentView';
import * as models from '../models';
import * as courseApi from '../api';
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

  // const asData = asIdx > -1 && asIdx < asList.length ? asList[asIdx] : null;

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

      <br />
      <br />

      {/* NOTE: UI for creating assignments not fully supported, easier to use DB client */}
      {isAdmin && (
        <Button variant="contained" onClick={handleCreateAs}>
          Create Assignment
        </Button>
      )}

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
                    value={asIdx >= 0 ? asIdx : false}
                    onChange={(
                      event: React.SyntheticEvent,
                      newValue: number
                    ) => {
                      setAsIdx(newValue);
                    }}
                    aria-label="Assignment Tabs"
                  >
                    {asList.map((as, idx) => (
                      <Tab
                        label={as.name}
                        value={idx}
                        key={as.id}
                        {...a11yProps(idx)}
                      />
                    ))}
                  </Tabs>
                </Box>
                {asList.map((as, idx) => (
                  <CustomTabPanel value={asIdx} index={idx} key={as.id}>
                    <AssignmentView asData={as} />
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
  index: number;
  value: number;
}

// https://mui.com/material-ui/react-tabs/#introduction
function CustomTabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
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
