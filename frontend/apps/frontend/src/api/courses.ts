import { jsonOrError, API_PATH } from './common';
import * as models from '../models';

const coursePath = `${API_PATH}/course`;

// MARK: courses
export const listCourses = async () => {
  return await jsonOrError(fetch(`${coursePath}/`, { method: 'GET' }));
};

export const getCourse = async (course_id: string) => {
  return await jsonOrError(
    fetch(`${coursePath}/${course_id}`, { method: 'GET' })
  );
};

// export const createCourse = async (id: string) => {
//   const url = `${basePath}/${id}`;
//   return await jsonOrError(fetch(url, { method: 'GET' }));
// };

// MARK: assignments
export const listAssignments = async (course_id: string) => {
  return await jsonOrError(
    fetch(`${coursePath}/${course_id}/assignment`, { method: 'GET' })
  );
};

export const getAssignment = async (
  course_id: string,
  assignment_id: string
) => {
  return await jsonOrError(
    fetch(`${coursePath}/${course_id}/assignment`, {
      method: 'GET',
    })
  );
};

export const createAssignment = async (
  course_id: string,
  attempt: models.AssignmentCreate
) => {
  return await jsonOrError(
    fetch(`${coursePath}/${course_id}/assignment`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(attempt),
    })
  );
};

// MARK: attempts
const attemptPath = `${API_PATH}/attempt`;

export const listAttempts = async (assignment_id: string) => {
  const params = new URLSearchParams({ assignment_id });
  return await jsonOrError(
    fetch(`${attemptPath}/?${params}`, { method: 'GET' })
  );
};

export const getAttempt = async (attempt_id: string) => {
  return await jsonOrError(
    fetch(`${attemptPath}/${attempt_id}`, { method: 'GET' })
  );
};

export const createAttempt = async (
  attempt: models.AttemptCreate
  // ): Promise<models.AttemptPublic | { error: string }> => {
) => {
  const params = new URLSearchParams({ assignment_id: attempt.assignment_id });

  return await jsonOrError(
    fetch(`${attemptPath}/?${params}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(attempt),
    })
  );
};
