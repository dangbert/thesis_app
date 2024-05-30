import { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  CardActions,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  DialogActions,
} from '@mui/material';
import { LOGIN_URL } from '../../constants';
import { useParams } from 'react-router-dom';
import * as models from '../../models';
import * as api from '../../api';
import * as constants from '../../constants';
import * as utils from '../../utils';
import { LoadingButton } from '@mui/lab';
import { useUserContext } from '../../providers';

interface UserProfileModalProps {
  open: boolean;
  onClose?: () => void;
  onUpdate: () => void; // callback after form is submitted
  course: models.CoursePublic;
}
/**
 * Component for user to join by invite key.
 */
const UserProfileModal: React.FC<UserProfileModalProps> = ({
  open,
  onClose,
  onUpdate,
  course,
}) => {
  const userCtx = useUserContext();
  const [groupNum, setGroupNum] = useState<number | null>(course.your_group);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!userCtx.user || utils.isUndefined(groupNum)) {
      return;
    }

    setSubmitting(true);
    setError('');
    const res = await api.setEnrollDetails(course.id, groupNum!);
    if (res.error) {
      setError(res.error);
    } else {
      onUpdate();
      if (onClose) onClose();
    }
    setSubmitting(false);
  };

  const canSubmit = !utils.isUndefined(groupNum);
  if (!userCtx) return <div>not logged in</div>;
  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="form-dialog-title"
      fullWidth={true}
      maxWidth="sm"
    >
      <DialogTitle id="form-dialog-title">Update Your Profile</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error">{error}</Alert>}
        <Typography>
          Please provide your group number for the course:
        </Typography>
        <Typography variant="caption" color="textSecondary">
          {course.name}
        </Typography>

        <br />
        <TextField
          sx={{ marginTop: '30px', maxWidth: '200px' }}
          type="number"
          label="Group Number"
          value={utils.isUndefined(groupNum) ? '' : groupNum}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
            const newGroupNum = parseInt(event.target.value);
            setGroupNum(isNaN(newGroupNum) ? null : newGroupNum);
          }}
          InputLabelProps={{
            shrink: true,
          }}
        />
      </DialogContent>
      <DialogActions>
        {onClose && (
          <Button onClick={onClose} color="primary">
            Cancel
          </Button>
        )}
        <LoadingButton
          onClick={handleSubmit}
          color="primary"
          loading={submitting}
          disabled={!canSubmit}
        >
          Save
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default UserProfileModal;
