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
  course: models.CoursePublic;
}
/**
 * Component for user to join by invite key.
 */
const UserProfileModal: React.FC<UserProfileModalProps> = ({
  open,
  onClose,
  course,
}) => {
  const userCtx = useUserContext();
  const [groupNum, setGroupNum] = useState<number | undefined>(
    userCtx.user?.group
  );
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = () => {};

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
          sx={{ marginTop: '10px', maxWidth: '200px' }}
          type="number"
          label="Group Number"
          value={groupNum} // Bind state to the TextField value
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
            console.log('event.target.value=', event.target.value);
            const newGroupNum = parseInt(event.target.value);
            if (isNaN(newGroupNum)) {
              console.log('isnan');
              setGroupNum(undefined);
            }
            setGroupNum(newGroupNum);
          }}
          InputLabelProps={{
            shrink: true, // Ensures the label does not overlap with the input value
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
