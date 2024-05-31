import { useEffect, useState } from 'react';
import { Button, Typography, Snackbar, Alert, Paper } from '@mui/material';
import AttemptCreateModal from './AttemptCreateModal';
import AttemptView from './AttemptView';
import AttemptHistory from './AttemptHistory';
import AssignmentStatus from './AssignmentStatus';
import Markdown from 'react-markdown';

import { AssignmentPublic } from '../models';
import * as models from '../models';
import * as courseApi from '../api';
import * as constants from '../constants';
import { useUserContext } from '../providers';
import UserAvatar from './user/UserAvatar';

interface IAssignmentViewProps {
  asData: AssignmentPublic;
  isTeacher: boolean;
  // dueDate: string;
}

const AssignmentView: React.FC<IAssignmentViewProps> = ({
  asData,
  isTeacher,
}) => {
  const [attempts, setAttempts] = useState<models.AttemptPublic[]>([]);
  const [error, setError] = useState<string>('');
  const [attemptLoadTime, setAttemptLoadTime] = useState<number>(
    Date.now() / 1000
  );
  const [loading, setLoading] = useState<boolean>(false);
  const userCtx = useUserContext();

  const [creatingAttempt, setCreatingAttempt] = useState(false);
  const [snackbarTxt, setSnackbarTxt] = useState('');

  // teacher's can view any student's submissions
  const [viewingStatus, setViewingStatus] =
    useState<models.AssignmentStudentStatus | null>(null);

  // user

  // load attempts
  useEffect(() => {
    let cancel = false;
    (async () => {
      if (!userCtx.user) return;
      setLoading(true);
      if (asData.id === '') {
        setAttempts([]);
        return;
      }
      setError('');
      const targetUserId = viewingStatus?.student.id || userCtx.user.id;
      const res = await courseApi.listAttempts(asData.id, targetUserId);
      if (cancel) return;
      if (res.error) {
        console.error(res.error);
        setError(`failed to load assignment submissions: ${res.error}`);
        setAttempts([]);
      } else {
        setAttempts(res.data);
      }
      setLoading(false);
      return () => (cancel = true);
    })();
  }, [asData.id, userCtx.user?.id, attemptLoadTime, viewingStatus]);

  if (!userCtx.user) return null;

  // user (other than current user) that's being viewed (if any)
  let spoofUser = viewingStatus?.student;
  if (spoofUser?.id === userCtx.user.id) spoofUser = undefined;

  let assignmentStatus = models.AssignmentAttemptStatus.NOT_STARTED;
  if (attempts.length > 0) {
    assignmentStatus = attempts[attempts.length - 1].status;
  }
  const canResubmit =
    assignmentStatus === models.AssignmentAttemptStatus.NOT_STARTED ||
    assignmentStatus === models.AssignmentAttemptStatus.RESUBMISSION_REQUESTED;

  return (
    <div>
      <Snackbar
        open={snackbarTxt !== ''}
        autoHideDuration={constants.SNACKBAR_DUR_MS}
        onClose={() => setSnackbarTxt('')}
        message={snackbarTxt}
      />

      <Typography variant="h5" component="h3">
        {asData.name}
      </Typography>

      <Markdown
        // make links open in a new page
        components={{
          a: ({ node, ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer" />
          ),
        }}
      >
        {asData.about}
      </Markdown>

      {error && <Alert severity="error">{error}</Alert>}

      {isTeacher && (
        <>
          <AssignmentStatus
            asData={asData}
            onSelectStudent={(studentStatus) => setViewingStatus(studentStatus)}
            // when attempts are updated here (e.g. after resubmission or feedback providedl)
            // also trigger the status table to update
            refreshTime={attemptLoadTime}
          />
          <br />
        </>
      )}

      <Paper
        sx={{ width: '100%', padding: '14px 14px 0px 14px' }}
        elevation={2}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Typography variant="h6" component="h4">
            {spoofUser ? `${spoofUser.name}'s` : 'Your'} submissions:
          </Typography>
          {/* make it very clear to the teacher who they're viewing */}
          {(spoofUser || isTeacher) && (
            <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
              <Typography sx={{ fontStyle: 'italic' }}>
                {(spoofUser || userCtx.user).email}
              </Typography>
              <UserAvatar user={spoofUser || userCtx.user} />
            </div>
          )}
        </div>
        {attempts.length === 0 && (
          <Alert
            severity="info"
            style={{ marginTop: '12px', marginBottom: '12px' }}
          >
            {spoofUser ? "They've" : "You've"} made no submissions on this
            assignment yet!
          </Alert>
        )}
        {!creatingAttempt && !spoofUser && canResubmit && (
          <Button
            variant="contained"
            onClick={() => setCreatingAttempt(true)}
            sx={{ marginTop: '14px' }}
          >
            New Submission
          </Button>
        )}
        <Typography>
          <b>{isTeacher ? 'Their' : 'Your'} Assignment Status</b>:{' '}
          {assignmentStatus}
        </Typography>

        {creatingAttempt && (
          <AttemptCreateModal
            asData={asData}
            open={creatingAttempt}
            onClose={() => setCreatingAttempt(false)}
            onCreate={(att: models.AttemptPublic) => {
              setAttemptLoadTime(Date.now() / 1000); // trigger formal refresh
              setSnackbarTxt('Attempt submitted ✅');
            }}
          />
        )}

        <AttemptHistory
          attempts={attempts}
          asData={asData}
          isTeacher={isTeacher}
          refreshAttempts={() => setAttemptLoadTime(Date.now() / 1000)}
        />
      </Paper>
    </div>
  );
};

export default AssignmentView;
