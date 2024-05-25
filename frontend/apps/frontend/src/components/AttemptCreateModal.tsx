import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  DialogActions,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Typography,
} from '@mui/material';
import { LoadingButton } from '@mui/lab';
import DeleteIcon from '@mui/icons-material/Delete';
import {
  AssignmentPublic,
  AttemptCreate,
  AttemptPublic,
  SMARTData,
} from '../models';
import * as courseApi from '../api';
import { useUserContext } from '../providers';
import * as constants from '../constants';
import FileView, { FileUploadButton } from './Files';

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
  onCreate,
}) => {
  // TODO: toast alert for error
  const [error, setError] = useState<string>('');
  const [data, setData] = useState<SMARTData>({ goal: '', plan: '' });
  const [submitting, setSubmitting] = useState<boolean>(false);
  const userCtx = useUserContext();
  const [files, setFiles] = useState<File[]>([]);

  const handleFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    console.log('received file:');
    console.log(event.target.files);
    // console.log(URL.createObjectURL(event.target.files[0]));
    if (event.target.files) {
      setFiles([...files, ...Array.from(event.target.files)]);
    }
  };

  const handleDeleteFile = (file: File) => {
    setFiles(files.filter((f) => f !== file));
  };

  const handleSubmit = async () => {
    if (!userCtx.user) {
      setError('User not logged in');
      return;
    }

    let cancelled = false;
    setSubmitting(true);

    // batch upload files
    const fileUploads = files.map((file) => courseApi.createFile(file));
    const fileResults = await Promise.all(fileUploads);
    let failedFiles = 0;
    const fileIds = [];
    console.log('fileResults', fileResults);
    for (const res of fileResults) {
      if (res.error) {
        failedFiles++;
      } else {
        fileIds.push(res.data.id);
      }
    }
    if (failedFiles) {
      setError(`Failed to upload ${failedFiles} files`);
      setSubmitting(false);
      return;
    }

    const attemptData: AttemptCreate = {
      assignment_id: asData.id,
      data,
      file_ids: fileIds,
    };
    const res = await courseApi.createAttempt(attemptData);
    if (cancelled) return;

    if (res.error) {
      setError('Failed to create attempt: ' + res.error);
      setSubmitting(false);
    } else {
      onCreate?.(res.data);
      onClose();
    }
    return () => (cancelled = true);
  };

  const canSubmit = !submitting && data.goal.trim() && data.plan.trim();

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
          minRows={constants.ATTEMPT_MIN_ROWS}
          maxRows={constants.ATTEMPT_MAX_ROWS}
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
          minRows={constants.ATTEMPT_MIN_ROWS}
          maxRows={constants.ATTEMPT_MAX_ROWS}
          name="plan"
          value={data.plan}
          onChange={handleFormChange}
        />

        <br />
        <br />
        <Typography variant="subtitle1" gutterBottom>
          File Attachments ({files.length}):
        </Typography>

        <FileUploadButton onChange={handleFileChange} />
        <List dense>
          {files.map((file, index) => (
            <ListItem key={index}>
              {/* <ListItemText primary={file.name} /> */}

              <FileView
                filename={file.name}
                read_url={URL.createObjectURL(file)}
              />
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={() => handleDeleteFile(file)}
                >
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Cancel
        </Button>
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
