import React, { useState, useContext } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  DialogActions,
  Button,
  CircularProgress,
} from '@mui/material';
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

    try {
      const response = await courseApi.createAttempt(attemptData);
      if (cancelled) return;

      if (response.error) {
        setError('Failed to create attempt: ' + response.error);
        setSubmitting(false);
      } else {
        onSubmit?.(response.data);
        onClose();
      }
    } catch (err: any) {
      if (!cancelled) {
        setError('An error occurred: ' + err.message);
        setSubmitting(false);
      }
    }

    return () => {
      cancelled = true;
    };
  };

  return (
    <Dialog open={open} onClose={onClose} aria-labelledby="form-dialog-title">
      <DialogTitle id="form-dialog-title">Create New Attempt</DialogTitle>
      <DialogContent>
        {error && <div style={{ color: 'red' }}>{error}</div>}
        <TextField
          autoFocus
          margin="dense"
          id="goal"
          label="Goal"
          type="text"
          fullWidth
          name="goal"
          value={data.goal}
          onChange={handleFormChange}
        />
        <TextField
          margin="dense"
          id="plan"
          label="Plan"
          type="text"
          fullWidth
          name="plan"
          value={data.plan}
          onChange={handleFormChange}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Cancel
        </Button>
        <Button onClick={handleSubmit} color="primary" disabled={submitting}>
          {submitting ? <CircularProgress size={24} /> : 'Submit'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AttemptCreateModal;
