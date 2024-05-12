import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  DialogActions,
  Button,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { LoadingButton } from '@mui/lab';
import {
  AssignmentPublic,
  AttemptCreate,
  AttemptPublic,
  SMARTData,
} from '../models';
import * as models from '../models';
import * as courseApi from '../api/courses';
import { useUserContext } from '../providers';

interface AttemptCreateModalProps {
  asData: AssignmentPublic;
  open: boolean;
  onClose: () => void;
  onCreate?: (attempt: AttemptPublic) => void;
}

const AttemptCreateModal: React.FC<AttemptCreateModalProps> = ({
  asData,
  open,
  onClose,
  onCreate: onSubmit,
}) => {
  const [error, setError] = useState<string>('');
  const [data, setData] = useState<SMARTData>({ goal: '', plan: '' });
  const [submitting, setSubmitting] = useState<boolean>(false);
  const userCtx = useUserContext();

  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('lg'));

  const handleFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async () => {
    if (!userCtx.user) {
      setError('User not logged in');
      return;
    }

    let cancelled = false;
    setSubmitting(true);
    const attemptData: AttemptCreate = {
      assignment_id: asData.id,
      user_id: userCtx.user.id,
      data,
    };

    const res = await courseApi.createAttempt(attemptData);
    if (cancelled) return;

    if (res.error) {
      setError('Failed to create attempt: ' + res.error);
      setSubmitting(false);
    } else {
      onSubmit?.(res.data);
      onClose();
    }
    return () => (cancelled = true);
  };

  const canSubmit = !submitting && data.goal && data.plan;
  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="form-dialog-title"
      fullWidth={true}
      maxWidth="md"
    >
      <DialogTitle id="form-dialog-title">Create New Attempt</DialogTitle>
      <DialogContent>
        {error && <div style={{ color: 'red' }}>{error}</div>}
        <TextField
          placeholder=""
          autoFocus
          margin="dense"
          id="goal"
          label="SMART Goal"
          type="text"
          fullWidth
          multiline
          rows={4}
          name="goal"
          value={data.goal}
          onChange={handleFormChange}
        />
        <TextField
          margin="dense"
          id="plan"
          label="Actieplan"
          type="text"
          fullWidth
          multiline
          rows={4}
          name="plan"
          value={data.plan}
          onChange={handleFormChange}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Cancel
        </Button>
        {/* loading spinner when submitting */}
        <LoadingButton
          onClick={handleSubmit}
          color="primary"
          loading={submitting}
          disabled={!canSubmit}
        >
          Submit
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default AttemptCreateModal;
