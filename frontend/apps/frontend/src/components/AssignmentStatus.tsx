import React from 'react';
import { useEffect, useState } from 'react';
import {
  Snackbar,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TableSortLabel,
  Toolbar,
  Typography,
  Paper,
  Checkbox,
  IconButton,
  Tooltip,
  Switch,
  Box,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
} from '@mui/material';
import { visuallyHidden } from '@mui/utils';
import { alpha } from '@mui/material/styles';
import DeleteIcon from '@mui/icons-material/Delete';
import FilterListIcon from '@mui/icons-material/FilterList';
import { LoadingButton } from '@mui/lab';

import AttemptCreateModal from './AttemptCreateModal';
import AttemptView from './AttemptView';
import AttemptHistory from './AttemptHistory';
import Markdown from 'react-markdown';

import { AssignmentPublic } from '../models';
import * as models from '../models';
import * as API from '../api';
import * as constants from '../constants';
import { useUserContext } from '../providers';
import * as utils from '../utils';

interface AssignmentStatusProps {
  asData: AssignmentPublic;
  // dueDate: string;
}

function descendingComparator<T>(a: T, b: T, orderBy: keyof T) {
  if (orderBy === 'last_attempt_date') {
    const dateA = new Date(a[orderBy] as string).getTime();
    const dateB = new Date(b[orderBy] as string).getTime();
    return dateB < dateA ? -1 : dateB > dateA ? 1 : 0;
  }
  if (b[orderBy] < a[orderBy]) {
    return -1;
  }
  if (b[orderBy] > a[orderBy]) {
    return 1;
  }
  return 0;
}

function getComparator<Key extends keyof any>(
  order: Order,
  orderBy: Key
): (
  a: { [key in Key]: number | string },
  b: { [key in Key]: number | string }
) => number {
  return order === 'desc'
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

type Order = 'asc' | 'desc';

interface RowData {
  id: string; // user id
  name: string;
  email: string;
  group: number;
  submissions: number;
  status: string;
  role: string;
  last_attempt_date: string;
}

interface HeadCell {
  disablePadding: boolean;
  id: keyof RowData;
  label: string;
  numeric: boolean;
}

const headCells: readonly HeadCell[] = [
  {
    id: 'name',
    numeric: false,
    disablePadding: true,
    label: 'Name',
  },
  {
    id: 'email',
    numeric: false,
    disablePadding: false,
    label: 'Email',
  },
  {
    id: 'role',
    numeric: false,
    disablePadding: false,
    label: 'role',
  },
  {
    id: 'group',
    numeric: true,
    disablePadding: false,
    label: 'Group',
  },
  {
    id: 'status',
    numeric: false,
    disablePadding: false,
    label: 'Assignment Status',
  },
  {
    id: 'submissions',
    numeric: true,
    disablePadding: false,
    label: 'Submissions',
  },
  {
    id: 'last_attempt_date',
    numeric: false,
    disablePadding: false,
    label: 'Last Submission',
  },
];

interface EnhancedTableProps {
  onRequestSort: (
    event: React.MouseEvent<unknown>,
    property: keyof RowData
  ) => void;
  order: Order;
  orderBy: string;
  rowCount: number;
}

// https://mui.com/material-ui/react-table/#sorting-amp-selecting
function EnhancedTableHead(props: EnhancedTableProps) {
  const { order, orderBy, rowCount, onRequestSort } = props;
  const createSortHandler =
    (property: keyof RowData) => (event: React.MouseEvent<unknown>) => {
      onRequestSort(event, property);
    };

  return (
    <TableHead>
      <TableRow>
        {headCells.map((headCell) => (
          <TableCell
            key={headCell.id}
            // align={headCell.numeric ? 'right' : 'left'}
            align={'left'}
            padding={headCell.disablePadding ? 'none' : 'normal'}
            sortDirection={orderBy === headCell.id ? order : false}
          >
            <TableSortLabel
              active={orderBy === headCell.id}
              direction={orderBy === headCell.id ? order : 'asc'}
              onClick={createSortHandler(headCell.id)}
            >
              {headCell.label}
              {orderBy === headCell.id ? (
                <Box component="span" sx={visuallyHidden}>
                  {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                </Box>
              ) : null}
            </TableSortLabel>
          </TableCell>
        ))}
      </TableRow>
    </TableHead>
  );
}

const AssignmentStatus: React.FC<AssignmentStatusProps> = ({ asData }) => {
  const [statusData, setStatusData] = useState<
    models.AssignmentStudentStatus[]
  >([]);
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [reloadTime, setReloadTime] = useState<number>(Date.now() / 1000);
  const userCtx = useUserContext();

  useEffect(() => {
    let cancel = false;
    (async () => {
      if (!userCtx.user) return;
      console.log(`requesting assignment status ${asData.id}`);

      setLoading(true);
      const res = await API.getAssignmentStatus(asData.course_id, asData.id);
      if (cancel) return;
      if (res.error) {
        console.error(res.error);
        setStatusData([]);
      } else {
        setStatusData(res.data);
      }
      setLoading(false);

      return () => (cancel = true);
    })();
  }, [asData.id, userCtx.user?.id, reloadTime]);

  const [groupFilter, setGroupFilter] = useState<'all' | 'even' | 'odd'>('all');
  const [order, setOrder] = React.useState<Order>('asc');
  const [orderBy, setOrderBy] = React.useState<keyof RowData>('name');
  const [page, setPage] = React.useState(0);
  const [dense, setDense] = React.useState(false);
  const [rowsPerPage, setRowsPerPage] = React.useState(-1); // show all

  const rows = statusData.map((s) => ({
    id: s.student.id,
    name: s.student.name,
    email: s.student.email,
    role: s.role,
    group: (utils.isUndefined(s.group_num) ? -1 : s.group_num) as number,
    submissions: s.attempt_count,
    last_attempt_date: s.last_attempt_date
      ? utils.friendlyDate(s.last_attempt_date)
      : '',
    status: s.status,
  }));

  const handleRequestSort = (
    event: React.MouseEvent<unknown>,
    property: keyof RowData
  ) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleChangeDense = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDense(event.target.checked);
  };

  const applyGroupFilter = (row: RowData) => {
    if (groupFilter === 'all') return true;
    if (groupFilter === 'even') return row.group % 2 === 0;
    return Math.abs(row.group % 2) === 1;
  };

  // Avoid a layout jump when reaching the last page with empty rows.
  const emptyRows =
    page > 0 ? Math.max(0, (1 + page) * rowsPerPage - rows.length) : 0;

  const visibleRows = React.useMemo(
    () =>
      rows
        .slice()
        .sort(getComparator(order, orderBy))
        .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
        .filter(applyGroupFilter),
    [JSON.stringify(statusData), order, orderBy, page, rowsPerPage, groupFilter]
  );

  const groupControls = (
    <FormControl component="fieldset">
      <FormLabel component="legend">Show Groups:</FormLabel>
      <RadioGroup
        row
        name="goal"
        value={groupFilter}
        onChange={(event) =>
          setGroupFilter(event.target.value as 'all' | 'even' | 'odd')
        }
      >
        <FormControlLabel
          value="all"
          control={<Radio />}
          label="All"
          // disabled={readOnly}
        />
        <FormControlLabel value="even" control={<Radio />} label="Even" />
        <FormControlLabel value="odd" control={<Radio />} label="Odd" />
      </RadioGroup>
    </FormControl>
  );

  // TODO: use MIT DataGrid! https://mui.com/x/react-data-grid/#mit-version-free-forever
  if (!userCtx.user) return null;
  return (
    <Paper
      sx={{ width: '100%', mb: 2, padding: '0px 14px 0px 14px' }}
      elevation={2}
    >
      {error && <Alert severity="error">{error}</Alert>}
      <Toolbar
        sx={{
          pl: { sm: 2 },
          pr: { xs: 1, sm: 1 },
        }}
      >
        <Typography
          sx={{ flex: '1 1 100%' }}
          variant="h6"
          id="tableTitle"
          component="div"
        >
          Course Members ({statusData.length})
        </Typography>
        <>
          {/* <Tooltip title="Filter list">
                <IconButton>
                  <FilterListIcon />
                </IconButton>
              </Tooltip> */}

          <Tooltip title="Filter list">
            <span>
              <LoadingButton
                onClick={() => setReloadTime(Date.now() / 1000)}
                color="primary"
                loading={loading}
                disabled={loading}
              >
                Refresh Table
              </LoadingButton>
            </span>
          </Tooltip>
        </>
      </Toolbar>
      <TableContainer sx={{ maxHeight: '60vh' }}>
        <Table
          sx={{ minWidth: 750 }}
          aria-labelledby="tableTitle"
          size={dense ? 'small' : 'medium'}
          stickyHeader
        >
          <EnhancedTableHead
            order={order}
            orderBy={orderBy}
            onRequestSort={handleRequestSort}
            rowCount={rows.length}
          />
          <TableBody>
            {visibleRows.map((row, index) => {
              return (
                <TableRow
                  hover
                  tabIndex={-1}
                  key={row.id}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell align="left">{row.name}</TableCell>
                  <TableCell align="left">
                    <a href={'mailto:' + row.email}>{row.email}</a>
                  </TableCell>
                  <TableCell align="left">{row.role}</TableCell>
                  <TableCell align="left">{row.group}</TableCell>
                  <TableCell align="left">{row.status}</TableCell>
                  <TableCell align="left">{row.submissions}</TableCell>
                  <TableCell align="left">{row.last_attempt_date}</TableCell>
                </TableRow>
              );
            })}
            {emptyRows > 0 && (
              <TableRow
                style={{
                  height: (dense ? 33 : 53) * emptyRows,
                }}
              >
                <TableCell colSpan={6} />
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      {rowsPerPage !== -1 && (
        <TablePagination
          rowsPerPageOptions={[25, 50, 100, { label: 'All', value: -1 }]}
          component="div"
          count={rows.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      )}
      <Box style={{ display: 'flex', gap: '36px', marginTop: '12px' }}>
        {groupControls}
        <FormControlLabel
          control={<Switch checked={dense} onChange={handleChangeDense} />}
          label="Dense padding"
        />
      </Box>
    </Paper>
  );
};

export default AssignmentStatus;
