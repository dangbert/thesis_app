import { jsonOrError, API_PATH } from './common';
import { AttemptCreate } from '../models';

const coursePath = `${API_PATH}/course`;

// MARK: courses
export const listCourses = async () => {
  return await jsonOrError(fetch(`${coursePath}/`, { method: 'GET' }));
};

export const getCourse = async (id: string) => {
  return await jsonOrError(fetch(`${coursePath}/${id}`, { method: 'GET' }));
};

// export const createCourse = async (id: string) => {
//   const url = `${basePath}/${id}`;
//   return await jsonOrError(fetch(url, { method: 'GET' }));
// };

// MARK: attempts
const attemptPath = `${API_PATH}/attempt`;

export const listAttempts = async (assignment_id: string) => {
  const params = new URLSearchParams({ assignment_id });
  return await jsonOrError(
    fetch(`${coursePath}/?${params}`, { method: 'GET' })
  );
};

export const createAttempt = async (
  assignment_id: string,
  attempt: AttemptCreate
) => {
  const formData = new FormData();
  for (const [key, value] of Object.entries(attempt)) {
    formData.append(key, value);
  }

  return await jsonOrError(
    fetch(attemptPath, {
      method: 'PUT',
      body: formData,
    })
  );
};

export const getAttempt = async (attempt_id: string) => {
  return await jsonOrError(
    fetch(`${coursePath}/${attempt_id}`, { method: 'GET' })
  );
};
