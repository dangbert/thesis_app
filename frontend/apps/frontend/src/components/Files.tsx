import * as models from '../models';
import { Button, Link } from '@mui/material';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

interface FileViewProps {
  file: models.FilePublic;
}

const FileView: React.FC<FileViewProps> = ({ file }) => {
  return (
    <Link href={file.read_url} target="_blank" rel="noreferrer">
      {file.filename}
    </Link>
  );
};

// https://mui.com/material-ui/react-button/#file-upload
const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

interface FileUploadButtonProps {
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export const FileUploadButton: React.FC<FileUploadButtonProps> = ({
  onChange,
}) => {
  return (
    <Button
      component="label"
      role={undefined}
      variant="outlined"
      tabIndex={-1}
      startIcon={<CloudUploadIcon />}
    >
      Upload file
      <VisuallyHiddenInput type="file" onChange={onChange} />
    </Button>
  );
};

export default FileView;
