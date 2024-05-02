import { AssignmentPublic } from '../models';

interface IAssignmentViewProps {
  data: AssignmentPublic;
  // dueDate: string;
}

const AssignmentView: React.FC<IAssignmentViewProps> = ({ data }) => {
  return <div>welcome to the assignment {data.name}</div>;
};

export default AssignmentView;
