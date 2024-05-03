import { useEffect, useState } from 'react';
import { Button } from '@mui/material';

import { AssignmentPublic } from '../models';
import * as models from '../models';
import * as courseApi from '../api/courses';

const DUMMY_ID = 'cc2d7ce4-170f-4817-b4a9-76e11d5f9c56';
interface IAssignmentViewProps {
  asData: AssignmentPublic;
  // dueDate: string;
}

const AssignmentView: React.FC<IAssignmentViewProps> = ({ asData }) => {
  const [attempts, setAttempts] = useState<models.AttemptPublic[]>([]);

  // load attempts
  useEffect(() => {
    console.log('at magic = ', asData.id);
    let cancel = false;
    (async () => {
      if (asData.id === '') {
        setAttempts([]);
        return;
      }
      console.log(`requesting attempts for assignment ${asData.id}`);
      const res = await courseApi.listAttempts(asData.id);
      if (cancel) return;
      if (res.error) {
        console.error(res.error);
        setAttempts([]);
      } else {
        console.log('fetched attempt list\n', res.data);
        setAttempts(res.data);
      }

      return () => (cancel = true);
    })();
  }, [asData.id]);

  // Function to handle button click to create an attempt
  const handleCreateAttempt = async () => {
    console.log('creating attempt');
    const dummySMART: models.SMARTData = {
      goal: 'Ik plan om mijn presentatietechniek te verbeteren door het gebruik van handgebaren.',
      plan: "Ik zal af en toe kijken naar video's van sprekers om te leren welke handgebaren zij gebruiken. Ik zal proberen deze gebaren te oefenen voor de spiegel wanneer ik tijd heb. Ik ga mijn vooruitgang beoordelen door na te denken over hoe zelfverzekerd ik me voel, en ik zal soms feedback vragen aan vrienden na presentaties.",
    };
    const dummyAttempt: models.AttemptCreate = {
      assignment_id: asData.id,
      user_id: DUMMY_ID,
      data: dummySMART,
    };
    const response = await courseApi.createAttempt(dummyAttempt);
    if (!response.error) {
      console.log('Attempt created:', response.data);
      setAttempts([...attempts, response.data]);
    } else {
      console.error('Error creating attempt:', response.error);
    }
  };

  return (
    <div>
      <div>
        welcome to the assignment {asData.name} (you have made {attempts.length}{' '}
        attempts)
      </div>
      <Button variant="contained" onClick={handleCreateAttempt}>
        Create Attempt
      </Button>
    </div>
  );
};

export default AssignmentView;
