import { useEffect, useState } from 'react';
import { Button, Typography, Snackbar } from '@mui/material';
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
  const [viewAttemptIdx, setViewAttemptIdx] = useState(-1);

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
      <div style={{ marginTop: '12px' }}>
        You have made {attempts.length} attempts so far on this assignment.
      </div>
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

      {attempts.length > 0 && viewAttemptIdx === -1 && (
        <Button
          variant="contained"
          onClick={() => setViewAttemptIdx(attempts.length - 1)}
        >
          View Last attempt
        </Button>
      )}
      {attempts.length > 0 && viewAttemptIdx > -1 && (
        <AttemptView
          attempt={attempts[viewAttemptIdx]}
          asData={asData}
          open={true}
          onClose={() => setViewAttemptIdx(-1)}
          mode={isInstructor ? 'createFeedback' : 'view'}
          onCreateFeedback={(feedback: models.FeedbackPublic) => {
            setSnackbarTxt('Feedback submitted ✅');
            setViewAttemptIdx(-1);
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
