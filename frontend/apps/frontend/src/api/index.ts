import { jsonOrError, API_PATH } from './common';
import * as models from '../models';

// MARK: auth
const authPath = `${API_PATH}/auth`;
export const LOGOUT_URL = `${authPath}/logout`;

/**
 * Note it's more user friendly to just link the user to LOGOUT_URL
 */
export const logout = async () => {
  return await jsonOrError(fetch(LOGOUT_URL, { method: 'GET' }));
};

export const getCurUser = async () => {
  return await jsonOrError(
    fetch(`${authPath}/me`, {
      method: 'GET',
    })
  );
};

// MARK: courses
const coursePath = `${API_PATH}/course`;
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

export const createFeedback = async (feedback: models.FeedbackCreate) => {
  return await jsonOrError(
    fetch(`${attemptPath}/${feedback.attempt_id}/feedback`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(feedback),
    })
  );
};

const filePath = `${API_PATH}/file`;
export const createFile = async (file: File) => {
  const url = `${filePath}/`;
  const formData = new FormData();
  formData.append('file', file);

  return await jsonOrError(
    fetch(url, {
      method: 'PUT',
      body: formData,
    })
  );
};
