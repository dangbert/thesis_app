import { useEffect, useState } from 'react';
import { Button, Typography, Snackbar, Alert } from '@mui/material';
import AttemptCreateModal from './AttemptCreateModal';
import AttemptView from './AttemptView';
import AttemptHistory from './AttemptHistory';

import { AssignmentPublic } from '../models';
import * as models from '../models';
import * as courseApi from '../api';
import * as constants from '../constants';
import { useUserContext } from '../providers';

interface IAssignmentViewProps {
  asData: AssignmentPublic;
  // dueDate: string;
}

const AssignmentView: React.FC<IAssignmentViewProps> = ({ asData }) => {
  const [attempts, setAttempts] = useState<models.AttemptPublic[]>([]);
  const userCtx = useUserContext();

  const [creatingAttempt, setCreatingAttempt] = useState(false);
  const [snackbarTxt, setSnackbarTxt] = useState('');

  const isInstructor = true; // TODO don't hardcode

  // load attempts
  useEffect(() => {
    let cancel = false;
    (async () => {
      if (!userCtx.user) return;
      if (asData.id === '') {
        setAttempts([]);
        return;
      }
      console.log(`requesting attempts for assignment ${asData.id}`);
      const res = await courseApi.listAttempts(asData.id, userCtx.user.id);
      if (cancel) return;
      if (res.error) {
        console.error(res.error);
        setAttempts([]);
      } else {
        console.log('fetched attempt list\n', res.data);
        setAttempts(res.data);
      }

      return () => (cancel = true);
    })();
  }, [asData.id, userCtx.user?.id]);

  if (!userCtx.user) return null;
  return (
    <div>
      <Snackbar
        open={snackbarTxt !== ''}
        autoHideDuration={constants.SNACKBAR_DUR_MS}
        onClose={() => setSnackbarTxt('')}
        message={snackbarTxt}
      />

      <Typography variant="h4" component="h2">
        {asData.name}
      </Typography>
      <Typography variant="body1" color="textSecondary" component="p">
        {asData.about}
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
        <Button variant="contained" onClick={() => setCreatingAttempt(true)}>
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
        isInstructor={isInstructor}
      />
    </div>
  );
};

export default AssignmentView;
