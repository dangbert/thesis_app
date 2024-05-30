import { useEffect, useState } from 'react';
import { Button, Typography, Snackbar, Alert } from '@mui/material';
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
  const userCtx = useUserContext();

  const [creatingAttempt, setCreatingAttempt] = useState(false);
  const [snackbarTxt, setSnackbarTxt] = useState('');

  // load attempts
  useEffect(() => {
    let cancel = false;
    (async () => {
      if (!userCtx.user) return;
      if (asData.id === '') {
        setAttempts([]);
        return;
      }
      setError('');
      const res = await courseApi.listAttempts(asData.id, userCtx.user.id);
      if (cancel) return;
      if (res.error) {
        console.error(res.error);
        setError(`failed to load assignment submissions: ${res.error}`);
        setAttempts([]);
      } else {
        setAttempts(res.data);
      }
      return () => (cancel = true);
    })();
  }, [asData.id, userCtx.user?.id, attemptLoadTime]);

  if (!userCtx.user) return null;
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
          <AssignmentStatus asData={asData} />
          <br />
        </>
      )}

      <Typography variant="h6" component="h4" style={{ marginTop: '24px' }}>
        Your submissions:
      </Typography>
      {attempts.length === 0 && (
        <Alert
          severity="info"
          style={{ marginTop: '12px', marginBottom: '12px' }}
        >
          You've made no submissions on this assignment yet!
        </Alert>
      )}
      {!creatingAttempt && (
        <Button
          variant="contained"
          onClick={() => setCreatingAttempt(true)}
          sx={{ marginTop: '14px' }}
        >
          New Submission
        </Button>
      )}

      {creatingAttempt && (
        <AttemptCreateModal
          asData={asData}
          open={creatingAttempt}
          onClose={() => setCreatingAttempt(false)}
          onCreate={(att: models.AttemptPublic) => {
            setAttempts((prev) => [...prev, att]);
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
    </div>
  );
};

export default AssignmentView;
