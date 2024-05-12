import { useEffect, useState } from 'react';
import { Button } from '@mui/material';
import Snackbar from '@mui/material/Snackbar';
import AttemptCreateModal from './AttemptCreateModal';
import AttemptView from './AttemptView';
import AttemptHistory from './AttemptHistory';

import { AssignmentPublic } from '../models';
import * as models from '../models';
import * as courseApi from '../api/courses';
import { useUserContext } from '../providers';

const DUMMY_ID = 'cc2d7ce4-170f-4817-b4a9-76e11d5f9c56';
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

  // load attempts
  useEffect(() => {
    let cancel = false;
    (async () => {
      if (asData.id === '') {
        setAttempts([]);
        return;
      }
      console.log(`requesting attempts for assignment ${asData.id}`);
      const res = await courseApi.listAttempts(asData.id);
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
  }, [asData.id]);

  if (!userCtx.user) {
    return <div>not logged in...</div>;
  }

  return (
    <div>
      <Snackbar
        open={snackbarTxt !== ''}
        autoHideDuration={4000}
        onClose={() => setSnackbarTxt('')}
        message={snackbarTxt}
      />

      <div>
        welcome {userCtx.user.name} to the assignment {asData.name} (you have
        made {attempts.length} attempts)
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

      {attempts.length && viewAttemptIdx === -1 && (
        <Button variant="contained" onClick={() => setViewAttemptIdx(0)}>
          View Last attempt
        </Button>
      )}
      {attempts.length && viewAttemptIdx > -1 && (
        <AttemptView
          attempt={attempts[viewAttemptIdx]}
          open={true}
          onClose={() => setViewAttemptIdx(-1)}
          mode="createFeedback"
          onCreateFeedback={(feedback: models.FeedbackPublic) => {
            setSnackbarTxt('Feedback submitted ✅');
            setViewAttemptIdx(-1);
          }}
        />
      )}

      <hr />
      <AttemptHistory attempts={attempts} />
    </div>
  );
};

export default AssignmentView;
