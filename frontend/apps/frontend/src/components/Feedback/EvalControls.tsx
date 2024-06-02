import { Paper, Typography } from '@mui/material';
import * as models from '../../models';
import { LikertStars } from './FormHelpers';

interface EvalControlsProps {
  evalData: models.EvalMetrics;
  onChange: (evalData: models.EvalMetrics) => void;
  readOnly: boolean;
}

/**
 * Form controls for teacher to optionally critique the AI feedback (for research purposes).
 */
const EvalControls: React.FC<EvalControlsProps> = ({
  evalData,
  onChange,
  readOnly,
}) => {
  return (
    <Paper variant="outlined" style={{ padding: '14px', marginTop: '7px' }}>
      <Typography variant="h6">AI Feedback Evaluation</Typography>
      <LikertStars
        value={evalData.rating || undefined}
        readOnly={readOnly}
        setValue={(newRating) => {
          onChange({ ...evalData, rating: newRating || null });
        }}
      />
    </Paper>
  );
};

export default EvalControls;
