import * as React from 'react';
import Rating from '@mui/material/Rating';
import Box from '@mui/material/Box';
import StarIcon from '@mui/icons-material/Star';
import { Theme, useTheme } from '@mui/material/styles';
import OutlinedInput from '@mui/material/OutlinedInput';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import Chip from '@mui/material/Chip';
import { Typography } from '@mui/material';

const STAR_LABELS: { [index: string]: string } = {
  1: 'Very dissatisfied',
  2: 'Dissatisfied',
  3: 'Unsure',
  4: 'Satisfied',
  5: 'Very satisfied',
};

function getLabelText(value: number) {
  return `${value} Star${value !== 1 ? 's' : ''}, ${STAR_LABELS[value]}`;
}

interface LikertStarsProps {
  value?: number;
  setValue(value?: number): void;
  readOnly: boolean;
  title: string;
}

// https://mui.com/material-ui/react-rating/#hover-feedback
export const LikertStars: React.FC<LikertStarsProps> = ({
  value,
  setValue,
  readOnly,
  title,
}) => {
  const [hover, setHover] = React.useState(-1);

  const curLabel =
    value !== undefined
      ? STAR_LABELS[value] ?? 'Not specified'
      : 'Not specified';

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <Typography sx={{ marginRight: '8px' }}>{title}:</Typography>
      <Rating
        name="hover-feedback"
        value={value}
        precision={1.0}
        getLabelText={getLabelText}
        readOnly={readOnly}
        onChange={(event, newValue) => {
          setValue(newValue || undefined);
        }}
        onChangeActive={(event, newHover) => {
          setHover(newHover);
        }}
        emptyIcon={<StarIcon style={{ opacity: 0.55 }} fontSize="inherit" />}
      />
      {value !== null && <Box sx={{ ml: 2 }}>{curLabel}</Box>}
    </Box>
  );
};

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

interface MultiSelectProps {
  selected: string[] | undefined;
  setSelected(selections: string[] | undefined): void;
  choices: string[];
  title: string;
  readOnly: boolean;
}

export const MultiSelect: React.FC<MultiSelectProps> = ({
  selected,
  setSelected,
  choices,
  title,
  readOnly,
}) => {
  const theme = useTheme();
  const handleChange = (event: SelectChangeEvent<typeof selected>) => {
    const {
      target: { value },
    } = event;
    const newSelected = typeof value === 'string' ? value.split(',') : value;
    setSelected(newSelected);
  };

  return (
    <div>
      <FormControl
        variant="outlined"
        sx={{ minWidth: '300px', maxWidth: '100%' }}
      >
        <InputLabel id="multi-select-label">{title}</InputLabel>
        <Select
          readOnly={readOnly}
          id="demo-multiple-chip"
          labelId="multi-select-label"
          multiple
          value={selected || []}
          onChange={handleChange}
          input={<OutlinedInput id="select-multiple-chip" label="Chip" />}
          renderValue={(selected) => (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {(selected || []).map((value) => (
                <Chip key={value} label={value} />
              ))}
            </Box>
          )}
          MenuProps={MenuProps}
        >
          {choices.map((name) => (
            <MenuItem
              key={name}
              value={name}
              style={getStyles(name, choices || [], theme)}
            >
              {name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </div>
  );
};

function getStyles(name: string, choices: readonly string[], theme: Theme) {
  return {
    fontWeight:
      (choices || []).indexOf(name) === -1
        ? theme.typography.fontWeightRegular
        : theme.typography.fontWeightMedium,
  };
}
